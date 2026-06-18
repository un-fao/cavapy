<p align="center">
  <img src="figures/cavapy_logo.svg" alt="cavapy logo" width="760">
</p>

<p align="center">
  <a href="https://pypi.org/project/cavapy/"><img src="https://img.shields.io/pypi/v/cavapy?label=PyPI&style=for-the-badge" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/cavapy"><img src="https://img.shields.io/pepy/dt/cavapy?style=for-the-badge&label=Downloads" alt="Total downloads"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-1f6feb?style=for-the-badge" alt="Python 3.11+">
</p>

<p align="center">
  Retrieve, subset, and process CORDEX-CORE and ERA5 climate data directly from THREDDS/OPeNDAP.
</p>

<p align="center">
  <a href="https://github.com/risk-team/cavapy/stargazers">Star this project on GitHub</a>
</p>

---

## What is cavapy?

Working with CORDEX-CORE climate projections normally means downloading terabytes of raw NetCDF files, reprojecting from rotated polar coordinates to regular lat/lon, writing boilerplate to handle non-Gregorian calendars, converting units, subsetting grids, wrangling multi-model ensembles, and layering bias correction on top. All before you can run a single analysis.

`cavapy` collapses all of that into one function call.

It streams only the spatial slice you need over OPeNDAP (no local archive required) and returns analysis-ready `xarray.DataArray` objects with consistent units, a standard Gregorian calendar, and optional bias correction already applied.

It is part of the [CAVA](https://risk-team.github.io/CAVAanalytics/articles/CAVA.html) (Climate and Agriculture Risk Visualization and Assessment) ecosystem, a joint initiative of FAO, the University of Cantabria, the University of Cape Town, and Predictia.

---

## What gets handled automatically

A single `get_climate_data()` call orchestrates a full pipeline:

| Step | What happens |
| --- | --- |
| **Inventory lookup** | Resolves the correct OPeNDAP URL(s) for your GCM/RCM/RCP/domain combination from a live THREDDS inventory |
| **Spatial subsetting** | Streams only the grid cells inside your country or bounding box — no full-file downloads |
| **Country → bbox** | Converts a country name to a precise bounding box using Natural Earth shapefiles |
| **Unit conversion** | K → °C for temperature; kg m⁻² s⁻¹ → mm/day for precipitation; J/m² → W/m² for solar radiation; 10 m → 2 m for wind speed |
| **Regridding** | CORDEX outputs are natively in rotated polar coordinates; the data served here has already been regridded to a regular lat/lon grid, so standard spatial operations work out of the box |
| **Calendar harmonization** | Converts 360-day and other non-Gregorian CORDEX calendars to Gregorian, filling gaps with NaN |
| **Parallelization** | Variables are fetched in parallel processes; within each process, threaded downloads handle multi-file retrieval |
| **Fault tolerance** | OPeNDAP connections retry up to 3 times with backoff; C-level noise is suppressed on intermediate attempts |
| **Bias correction** | ERA5 is automatically fetched as the reference; EQM is trained and applied — no external tools needed |
| **Domain validation** | If your bounding box falls outside the chosen CORDEX domain, a corrected domain is suggested |

---

## Data Coverage

### Sources

- CORDEX-CORE regional climate simulations (25 km)
- ERA5 reanalysis (used directly and as the reference for bias correction)

Data is hosted on the University of Cantabria THREDDS infrastructure.

### Available datasets

- **`CORDEX-CORE`** — original model outputs. Use this when you want raw projections or when you will apply your own post-processing.
- **`CORDEX-CORE-BC`** — pre-bias-corrected outputs. The full CORDEX-CORE archive was corrected against ERA5 reanalysis using the [ISIMIP3 methodology](https://www.isimip.org/documents/413/ISIMIP3b_bias_adjustment_fact_sheet_GCMs_v2.pdf) (trend-preserving quantile mapping). Use this dataset when you need a consistent, ready-to-use ensemble with no additional processing.

### Available variables

| Variable | Description | Units |
| --- | --- | --- |
| `tas` | Daily mean temperature | °C |
| `tasmax` | Daily maximum temperature | °C |
| `tasmin` | Daily minimum temperature | °C |
| `pr` | Daily precipitation | mm/day |
| `hurs` | Daily relative humidity | % |
| `sfcWind` | Daily wind speed at 2 m | m/s |
| `rsds` | Daily solar radiation | W/m² |

### Supported domains and scenario/model options

- **Domains**: `NAM-22`, `EUR-22`, `AFR-22`, `EAS-22`, `SEA-22`, `WAS-22`, `AUS-22`, `SAM-22`, `CAM-22`
- **RCPs**: `rcp26`, `rcp85`
- **GCMs**: `MOHC`, `MPI`, `NCC`
- **RCMs**: `REMO`, `Reg`

---

## Installation

```bash
conda create -n cavapy "python>=3.11"
conda activate cavapy
pip install cavapy
```

---

## Quick Start

### 1) Pre-bias-corrected projections (recommended)

Uses `CORDEX-CORE-BC`: the full CORDEX archive already corrected against ERA5 using the ISIMIP3 methodology. No further correction is applied at download time.

```python
import cavapy

togo = cavapy.get_climate_data(
    country="Togo",
    variables=["tasmax", "pr"],
    cordex_domain="AFR-22",
    rcp="rcp26",
    gcm="MPI",
    rcm="REMO",
    years_up_to=2030,
    dataset="CORDEX-CORE-BC",
)
# Returns: {"tasmax": xr.DataArray, "pr": xr.DataArray}
```

### 2) Original CORDEX-CORE with on-the-fly bias correction

When `bias_correction=True`, cavapy automatically fetches ERA5 for the historical period and applies **Empirical Quantile Mapping (EQM)** via [xsdba](https://xsdba.readthedocs.io). Historical bias correction uses leave-one-out cross-validation to avoid overfitting. Multiplicative scaling is applied for precipitation, wind, and radiation; additive for temperature and humidity. This is useful when you need custom period or region coverage beyond the pre-corrected archive.

```python
import cavapy

togo = cavapy.get_climate_data(
    country="Togo",
    variables=["tasmax", "pr"],
    cordex_domain="AFR-22",
    rcp="rcp26",
    gcm="MPI",
    rcm="REMO",
    years_up_to=2030,
    bias_correction=True,
    dataset="CORDEX-CORE",
)
```

### 3) ERA5 observations only

```python
import cavapy

era5 = cavapy.get_climate_data(
    country="Togo",
    variables=["tasmax", "pr"],
    obs=True,
    years_obs=range(1980, 2019),
)
```

---

## Core Workflows

### Projections + historical baseline

Setting `historical=True` fetches the 1980–2005 historical simulation run and concatenates it with the projection period, giving a continuous time series.

```python
import cavapy

data = cavapy.get_climate_data(
    country="Afghanistan",
    variables=["tasmax", "pr"],
    cordex_domain="WAS-22",
    rcp="rcp85",
    gcm="NCC",
    rcm="REMO",
    years_up_to=2030,
    historical=True,
    dataset="CORDEX-CORE-BC",
)
```

### Multi-model ensemble

Pass lists (or `None` for all) to `rcp`, `gcm`, and `rcm`. Invalid combinations for the domain are skipped automatically with a warning, rather than raising an error.

```python
import cavapy

multi = cavapy.get_climate_data(
    country="Togo",
    cordex_domain="AFR-22",
    rcp=["rcp26", "rcp85"],
    gcm=["MPI", "MOHC"],
    rcm=["Reg", "REMO"],
    years_up_to=2030,
    historical=True,
    dataset="CORDEX-CORE-BC",
)
```

The return structure for multi-combination requests is a nested dict:

```python
multi[rcp][f"{gcm}-{rcm}"][variable]  # -> xarray.DataArray
```

### Custom bounding box

```python
import cavapy

data = cavapy.get_climate_data(
    country=None,
    xlim=(30.0, 42.0),
    ylim=(3.0, 15.0),
    cordex_domain="AFR-22",
    rcp="rcp85",
    gcm="MPI",
    rcm="REMO",
    years_up_to=2050,
    buffer=1,  # expand bbox by 1 degree on each side
)
```

---

## Parallelization

`get_climate_data()` uses two levels of concurrency:

- **Single model/scenario**: variables are processed in parallel across processes (default: one per variable), with threaded downloads inside each process
- **Multiple models/scenarios**: combo × variable tasks are distributed across a global process pool (default cap: 6 processes); a live progress bar tracks completion
- Sequential mode is used when `num_processes <= 1` or only one variable is requested

### macOS and Windows scripts

On macOS and Windows, Python starts multiprocessing workers with the `spawn` method. This means each worker imports the script again before running its task. If `get_climate_data()` is called at the top level of a `.py` script, that import re-runs the same call while Python is still starting the worker process, which can raise a multiprocessing bootstrapping `RuntimeError`.

When using multiple variables or multi-model requests in a script on macOS or Windows, put the call behind Python's standard multiprocessing entry-point guard:

```python
import cavapy


def main():
    togo = cavapy.get_climate_data(
        country="Togo",
        variables=["tasmax", "pr"],
        cordex_domain="AFR-22",
        rcp="rcp26",
        gcm="MPI",
        rcm="REMO",
        years_up_to=2030,
        dataset="CORDEX-CORE-BC",
    )
    return togo


if __name__ == "__main__":
    main()
```

For a quick unguarded script, use `num_processes=1` or request a single variable to run sequentially.

---

## Plotting

`cavapy` includes built-in plotting helpers that work directly on the returned DataArrays.

### Spatial map

```python
import cavapy

data = cavapy.get_climate_data(country="Togo", obs=True, years_obs=range(1990, 2011))

fig = cavapy.plot_spatial_map(
    data["tasmax"],
    time_period=(2000, 2010),
    title="Mean Max Temperature 2000-2010",
    cmap="Reds",
)
```

![Spatial temperature map](figures/spatial_map_temperature.png)

### Time series

```python
fig = cavapy.plot_time_series(
    data["pr"],
    title="Precipitation Time Series - Togo (1990-2011)",
    trend_line=True,
    ylabel="Annual Precipitation (mm)",
    aggregation="sum",
    figsize=(12, 6),
)
```

![Precipitation time series](figures/time_series_precipitation.png)

For advanced visualization and reporting, see [CAVAanalytics](https://risk-team.github.io/CAVAanalytics/).

---

## Operational Notes

- Check [GitHub issues](https://github.com/risk-team/cavapy/issues) for data server outages or announcements. cavapy fetches these automatically at startup.
- Set `CAVAPY_NO_ANNOUNCEMENTS=1` to disable startup announcements in scripts or production runs.

---

## Citation and License

- License: [MIT](LICENSE)
- Package metadata and build details: [pyproject.toml](pyproject.toml)
