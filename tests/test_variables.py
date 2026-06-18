import importlib


def test_tas_is_supported(monkeypatch):
    import cavapy
    from cavapy.cava_config import VARIABLES_MAP

    cavapy_module = importlib.import_module("cavapy.cavapy")

    monkeypatch.setattr(cavapy_module, "_show_startup_announcements", lambda: None)
    monkeypatch.setattr(cavapy_module, "_validate_urls", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        cavapy_module,
        "_geo_localize",
        lambda *args, **kwargs: {"xlim": (0.0, 1.0), "ylim": (0.0, 1.0)},
    )
    monkeypatch.setattr(
        cavapy_module,
        "process_worker",
        lambda *args, variable=None, **kwargs: f"processed:{variable}",
    )

    assert "tas" in cavapy.VALID_VARIABLES
    assert VARIABLES_MAP["tas"] == "t2m"

    data = cavapy.get_climate_data(
        country="Togo",
        variables=["tas", "pr"],
        cordex_domain="AFR-22",
        rcp="rcp26",
        gcm="MPI",
        rcm="REMO",
        years_up_to=2030,
        dataset="CORDEX-CORE-BC",
        num_processes=1,
    )

    assert data == {"tas": "processed:tas", "pr": "processed:pr"}
