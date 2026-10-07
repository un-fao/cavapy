import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import xarray as xr

import cavapy.cava_download as cava_download


class TestDownloadMaterialization(unittest.TestCase):
    @staticmethod
    def _source_data():
        time = pd.date_range("2005-01-01", "2007-12-31", freq="D")
        return xr.Dataset(
            {
                "tas": (
                    ("time", "latitude", "longitude"),
                    np.full((time.size, 2, 2), 300.0),
                    {"units": "K"},
                )
            },
            coords={
                "time": time,
                "latitude": [8.0, 8.25],
                "longitude": [0.0, 0.25],
            },
        )

    def test_subset_is_loaded_without_dask_chunks(self):
        source = self._source_data()
        open_kwargs = []

        def _open_dataset(url, **kwargs):
            open_kwargs.append(kwargs)
            return source.copy()

        with patch.object(cava_download.xr, "open_dataset", _open_dataset):
            result = cava_download._download_data(
                url="https://example.test/data_rcp26.nc",
                bbox={"xlim": (0.0, 0.25), "ylim": (8.0, 8.25)},
                variable="tas",
                obs=False,
                years_obs=range(1980, 2006),
                years_up_to=2007,
                remote=True,
                gcm="MPI",
                rcm="REMO",
                rcp="rcp26",
            )

        self.assertEqual(open_kwargs, [{}])
        self.assertEqual(set(result.time.dt.year.values), {2006, 2007})
        self.assertIsInstance(result.data, np.ndarray)
        self.assertEqual(result.attrs["units"], "°C")
        result.interpolate_na(dim="time", method="linear")

    def test_unit_conversion_can_be_disabled(self):
        source = self._source_data()

        with patch.object(
            cava_download.xr, "open_dataset", lambda url, **kwargs: source.copy()
        ):
            result = cava_download._download_data(
                url="https://example.test/data_rcp26.nc",
                bbox={"xlim": (0.0, 0.25), "ylim": (8.0, 8.25)},
                variable="tas",
                obs=False,
                years_obs=range(1980, 2006),
                years_up_to=2007,
                remote=True,
                gcm="MPI",
                rcm="REMO",
                rcp="rcp26",
                convert_units=False,
            )

        np.testing.assert_array_equal(result.values, 300.0)
        self.assertEqual(result.attrs["units"], "K")


if __name__ == "__main__":
    unittest.main()
