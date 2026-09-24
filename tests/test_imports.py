import logging
import unittest


class TestImports(unittest.TestCase):
    def test_public_api_is_exposed(self):
        import cavapy

        self.assertTrue(hasattr(cavapy, "get_climate_data"))
        self.assertTrue(hasattr(cavapy, "plot_spatial_map"))
        self.assertTrue(hasattr(cavapy, "plot_time_series"))

    def test_climate_logger_does_not_propagate_to_root(self):
        import cavapy

        climate = logging.getLogger("climate")
        self.assertTrue(climate.handlers)
        self.assertFalse(climate.propagate)

        class CountingHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []

            def emit(self, record):
                self.records.append(record)

        root = logging.getLogger()
        root_counter = CountingHandler()
        root.addHandler(root_counter)
        previous_level = root.level
        root.setLevel(logging.DEBUG)
        try:
            climate.getChild("MPI-REMO-pr-rcp26").info("Connection established")
        finally:
            root.removeHandler(root_counter)
            root.setLevel(previous_level)

        self.assertEqual(root_counter.records, [])


if __name__ == "__main__":
    unittest.main()
