import sys
import types
import unittest

import numpy as np
import pandas as pd
import xarray as xr

sys.modules.setdefault(
    "xsdba",
    types.SimpleNamespace(EmpiricalQuantileMapping=types.SimpleNamespace()),
)

from cavapy.cava_config import logger
from cavapy.cava_download import _select_spatial_subset


def _data_array(latitude, longitude):
    values = np.arange(len(latitude) * len(longitude), dtype=float).reshape(
        1, len(latitude), len(longitude)
    )
    return xr.DataArray(
        values,
        dims=("time", "latitude", "longitude"),
        coords={
            "time": pd.date_range("2006-01-01", periods=1),
            "latitude": latitude,
            "longitude": longitude,
        },
    )


class TestSpatialSelection(unittest.TestCase):
    def test_selects_ascending_latitude(self):
        data = _data_array(latitude=[0.0, 0.5, 1.0], longitude=[10.0, 10.5, 11.0])

        subset = _select_spatial_subset(
            data,
            {"xlim": (10.2, 10.8), "ylim": (0.2, 0.8)},
            logger,
        )

        self.assertEqual(subset.sizes["latitude"], 1)
        self.assertEqual(subset.sizes["longitude"], 1)
        self.assertEqual(float(subset.latitude.values[0]), 0.5)
        self.assertEqual(float(subset.longitude.values[0]), 10.5)

    def test_selects_descending_latitude(self):
        data = _data_array(latitude=[1.0, 0.5, 0.0], longitude=[10.0, 10.5, 11.0])

        subset = _select_spatial_subset(
            data,
            {"xlim": (10.2, 10.8), "ylim": (0.2, 0.8)},
            logger,
        )

        self.assertEqual(subset.sizes["latitude"], 1)
        self.assertEqual(subset.sizes["longitude"], 1)
        self.assertEqual(float(subset.latitude.values[0]), 0.5)
        self.assertEqual(float(subset.longitude.values[0]), 10.5)

    def test_selects_descending_longitude(self):
        data = _data_array(latitude=[0.0, 0.5, 1.0], longitude=[11.0, 10.5, 10.0])

        subset = _select_spatial_subset(
            data,
            {"xlim": (10.2, 10.8), "ylim": (0.2, 0.8)},
            logger,
        )

        self.assertEqual(subset.sizes["latitude"], 1)
        self.assertEqual(subset.sizes["longitude"], 1)
        self.assertEqual(float(subset.latitude.values[0]), 0.5)
        self.assertEqual(float(subset.longitude.values[0]), 10.5)

    def test_falls_back_to_nearest_when_bbox_has_no_grid_center(self):
        data = _data_array(latitude=[0.0, 1.0], longitude=[10.0, 11.0])

        subset = _select_spatial_subset(
            data,
            {"xlim": (10.2, 10.3), "ylim": (0.2, 0.3)},
            logger,
        )

        self.assertEqual(subset.sizes["latitude"], 1)
        self.assertEqual(subset.sizes["longitude"], 1)
        self.assertEqual(float(subset.latitude.values[0]), 0.0)
        self.assertEqual(float(subset.longitude.values[0]), 10.0)


if __name__ == "__main__":
    unittest.main()
