import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import numpy as np
import pandas as pd
import xarray as xr

import cavapy.cava_download as cava_download
import cavapy.cava_validation as cava_validation
from cavapy.cava_validation import _filter_inventory


def _inventory(rows):
    return pd.DataFrame(
        rows,
        columns=["activity", "domain", "model", "rcm", "experiment", "location", "hub"],
    )


_BASE_ROWS = [
    ("FAO CORDEX", "AFR-22", "MPI-M-MPI-ESM-LR", "REMO2015", "historical", "url-hist", "hub-hist"),
    ("FAO CORDEX", "AFR-22", "MPI-M-MPI-ESM-LR", "REMO2015", "rcp26", "url-rcp26", "hub-rcp26"),
    ("CRDX-ISIMIP-025", "AFR-22", "MPI-M-MPI-ESM-LR", "REMO2015", "rcp26", "url-bc", "hub-bc"),
]


class TestFilterInventory(unittest.TestCase):
    def test_returns_one_row_per_experiment(self):
        with patch.object(
            cava_validation, "_read_inventory", lambda url: _inventory(_BASE_ROWS)
        ):
            filtered, column = _filter_inventory(
                remote=True,
                dataset="CORDEX-CORE",
                cordex_domain="AFR-22",
                gcm="MPI",
                rcm="REMO",
                experiments=["rcp26", "historical"],
            )

        self.assertEqual(column, "location")
        self.assertEqual(
            dict(zip(filtered["experiment"], filtered["location"])),
            {"historical": "url-hist", "rcp26": "url-rcp26"},
        )

    def test_local_inventory_uses_hub_column(self):
        with patch.object(
            cava_validation, "_read_inventory", lambda url: _inventory(_BASE_ROWS)
        ):
            filtered, column = _filter_inventory(
                remote=False,
                dataset="CORDEX-CORE",
                cordex_domain="AFR-22",
                gcm="MPI",
                rcm="REMO",
                experiments=["rcp26"],
            )

        self.assertEqual(column, "hub")
        self.assertEqual(list(filtered["hub"]), ["hub-rcp26"])

    def test_no_match_raises_informative_error(self):
        with patch.object(
            cava_validation, "_read_inventory", lambda url: _inventory(_BASE_ROWS)
        ):
            with self.assertRaisesRegex(ValueError, "No CORDEX entries found"):
                _filter_inventory(
                    remote=True,
                    dataset="CORDEX-CORE",
                    cordex_domain="EUR-22",
                    gcm="MPI",
                    rcm="REMO",
                    experiments=["rcp26"],
                )

    def test_ambiguous_match_raises(self):
        # Two rcp26 rows match the same substring filters.
        rows = _BASE_ROWS + [
            ("FAO CORDEX", "AFR-22", "MPI-M-MPI-ESM-MR", "REMO2015", "rcp26", "url-mr", "hub-mr"),
        ]
        with patch.object(
            cava_validation, "_read_inventory", lambda url: _inventory(rows)
        ):
            with self.assertRaisesRegex(ValueError, "Ambiguous inventory match"):
                _filter_inventory(
                    remote=True,
                    dataset="CORDEX-CORE",
                    cordex_domain="AFR-22",
                    gcm="MPI",
                    rcm="REMO",
                    experiments=["rcp26", "historical"],
                )


class TestObservationPath(unittest.TestCase):
    def test_obs_request_does_not_read_the_cordex_inventory(self):
        def _fail_read(url):
            raise AssertionError("obs=True must not read the CORDEX inventory")

        time = pd.date_range("1990-01-01", "1990-12-31", freq="D")
        era5 = xr.DataArray(
            np.ones(time.size), dims=("time",), coords={"time": time}
        )

        with (
            patch.object(cava_validation, "_read_inventory", _fail_read),
            patch.object(
                cava_download, "_thread_download_data", lambda url=None, **kwargs: era5
            ),
            ThreadPoolExecutor(max_workers=1) as executor,
        ):
            result = cava_download._climate_data_for_variable(
                executor,
                variable="tas",
                bbox={"xlim": (0.0, 1.0), "ylim": (0.0, 1.0)},
                cordex_domain="AFR-22",
                rcp="rcp26",
                gcm="MPI",
                rcm="REMO",
                years_up_to=2030,
                years_obs=range(1990, 1991),
                obs=True,
                bias_correction=False,
                historical=False,
                remote=True,
            )

        self.assertTrue(result.identical(era5))


if __name__ == "__main__":
    unittest.main()
