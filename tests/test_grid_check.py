import unittest

import numpy as np
import xarray as xr

from cavapy.cava_download import _ensure_geographic_grid


def _dataset(lat1d, lon1d, lat2d=None, lon2d=None):
    coords = {"latitude": list(lat1d), "longitude": list(lon1d)}
    if lat2d is not None:
        coords["lat"] = (("latitude", "longitude"), lat2d)
        coords["lon"] = (("latitude", "longitude"), lon2d)
    return xr.Dataset(
        {"tas": (("latitude", "longitude"), np.zeros((len(lat1d), len(lon1d))))},
        coords=coords,
    )


class TestEnsureGeographicGrid(unittest.TestCase):
    def test_regular_grid_passes(self):
        ds = _dataset([10.0, 10.25, 10.5], [40.0, 40.25, 40.5])
        _ensure_geographic_grid(ds, ds["tas"], "url")

    def test_regular_grid_with_consistent_2d_coords_passes(self):
        lat1d = np.array([10.0, 10.25, 10.5])
        lon1d = np.array([40.0, 40.25, 40.5])
        lat2d = np.broadcast_to(lat1d[:, None], (3, 3))
        lon2d = np.broadcast_to(lon1d[None, :], (3, 3))
        ds = _dataset(lat1d, lon1d, lat2d, lon2d)
        _ensure_geographic_grid(ds, ds["tas"], "url")

    def test_projected_meter_coordinates_are_rejected(self):
        # RegCM-style axes in meters.
        ds = _dataset([-3075000.0, 0.0, 3075000.0], [-4750000.0, 0.0, 4750000.0])
        with self.assertRaisesRegex(ValueError, "not on a regular"):
            _ensure_geographic_grid(ds, ds["tas"], "url")

    def test_rotated_pole_coordinates_are_rejected(self):
        # REMO-style rotated axes: plausible degrees, but the 2-D geographic
        # 'lat' array tells a different story.
        lat1d = np.array([-1.0, 0.0, 1.0])
        lon1d = np.array([-1.0, 0.0, 1.0])
        lat2d = np.full((3, 3), 40.0)
        lon2d = np.full((3, 3), 140.0)
        ds = _dataset(lat1d, lon1d, lat2d, lon2d)
        with self.assertRaisesRegex(ValueError, "not on a regular"):
            _ensure_geographic_grid(ds, ds["tas"], "url")


if __name__ == "__main__":
    unittest.main()
