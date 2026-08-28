import unittest


class TestImports(unittest.TestCase):
    def test_public_api_is_exposed(self):
        import cavapy

        self.assertTrue(hasattr(cavapy, "get_climate_data"))
        self.assertTrue(hasattr(cavapy, "plot_spatial_map"))
        self.assertTrue(hasattr(cavapy, "plot_time_series"))


if __name__ == "__main__":
    unittest.main()
