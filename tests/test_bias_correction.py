import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import numpy as np
import pandas as pd
import xarray as xr

import cavapy.cava_download as cava_download
import cavapy.cava_validation as cava_validation


def _daily_series(start, end, offset):
    time = pd.date_range(start, end, freq="D")
    day_of_year = time.dayofyear.values.astype(float)
    values = 10.0 + 5.0 * np.sin(2 * np.pi * day_of_year / 365.25) + offset
    data = xr.DataArray(values, dims=("time",), coords={"time": time})
    data.attrs["units"] = "degC"
    return data


_FAKE_INVENTORY = pd.DataFrame(
    {
        "activity": ["FAO CORDEX", "FAO CORDEX"],
        "domain": ["AFR-22", "AFR-22"],
        "model": ["MPI-M-MPI-ESM-LR", "MPI-M-MPI-ESM-LR"],
        "rcm": ["REMO2015", "REMO2015"],
        "experiment": ["historical", "rcp26"],
        "location": ["url-historical", "url-rcp26"],
        "hub": ["url-historical", "url-rcp26"],
    }
)

_PROJECTION_OFFSET = 5.0


def _fake_thread_download_data(url=None, **kwargs):
    if kwargs.get("obs"):
        # ERA5 reference, identical to the historical run: the model is unbiased.
        return _daily_series("1980-01-01", "2005-12-31", offset=0.0)
    if "historical" in url:
        return _daily_series("1980-01-01", "2005-12-31", offset=0.0)
    # Projection carries a +5 degC climate-change signal relative to historical.
    return _daily_series("2006-01-01", "2010-12-31", offset=_PROJECTION_OFFSET)


class TestBiasCorrection(unittest.TestCase):
    def test_projection_correction_trains_on_historical_run(self):
        """With an unbiased model, bias correction must not alter the projection.

        Training the quantile mapping on the projection itself (instead of the
        historical run) would remove the climate-change signal from the output.
        """
        with (
            patch.object(
                cava_validation, "_read_inventory", lambda url: _FAKE_INVENTORY.copy()
            ),
            patch.object(
                cava_download, "_thread_download_data", _fake_thread_download_data
            ),
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            corrected = cava_download._climate_data_for_variable(
                executor,
                variable="tas",
                bbox={"xlim": (0.0, 1.0), "ylim": (0.0, 1.0)},
                cordex_domain="AFR-22",
                rcp="rcp26",
                gcm="MPI",
                rcm="REMO",
                years_up_to=2010,
                years_obs=range(1980, 2006),
                obs=False,
                bias_correction=True,
                historical=False,
                remote=True,
            )

        projection = _daily_series("2006-01-01", "2010-12-31", offset=_PROJECTION_OFFSET)
        # Bias is zero by construction, so the corrected projection must keep the
        # +5 degC signal. The buggy training on the projection collapses it back
        # onto the reference climatology (~offset 0).
        self.assertLess(
            abs(float(corrected.mean()) - float(projection.mean())),
            0.5,
        )


if __name__ == "__main__":
    unittest.main()
