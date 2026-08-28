"""Validation helpers for input parameters and spatial domain checks."""

import logging
from functools import lru_cache

import pandas as pd
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader

from .cava_config import (
    ERA5_DATA_REMOTE_URL,
    INVENTORY_DATA_LOCAL_PATH,
    INVENTORY_DATA_REMOTE_URL,
    VALID_GCM,
    VALID_RCM,
    logger,
)


def _ensure_inventory_not_empty(
    filtered_data: pd.DataFrame,
    *,
    dataset: str,
    cordex_domain: str,
    gcm: str,
    rcm: str,
    experiments: list[str],
    activity_filter: str,
    log: logging.Logger | None = None,
) -> None:
    """
    Ensure that the inventory filter returned at least one URL.
    If not, raise a clear, informative error instead of failing later with iloc[0].
    """
    if not filtered_data.empty:
        return

    msg = (
        "No CORDEX entries found in the inventory for the requested configuration.\n"
        f"  dataset        : {dataset}\n"
        f"  domain         : {cordex_domain}\n"
        f"  gcm            : {gcm}\n"
        f"  rcm            : {rcm}\n"
        f"  experiments    : {experiments}\n"
        f"  activity_filter: {activity_filter}\n\n"
        "This usually means that this GCM/RCM/experiment combination does not exist "
        "or that ther is an issue with the inventory data.\n"
        "Please check the inventory CSV at https://hub.ipcc.ifca.es/thredds/fileServer/inventories/cava.csv"
    )

    if log is not None:
        log.error(msg)

    raise ValueError(msg)


@lru_cache(maxsize=None)
def _read_inventory(csv_path_or_url: str) -> pd.DataFrame:
    """Read the inventory CSV once per process and reuse it across requests."""
    return pd.read_csv(csv_path_or_url)


def _filter_inventory(
    *,
    remote: bool,
    dataset: str,
    cordex_domain: str,
    gcm: str,
    rcm: str,
    experiments: list[str],
    log: logging.Logger | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Return the inventory rows matching the request and the URL column to use.

    Raises:
        ValueError: If no rows match, or if more than one dataset matches a
            single experiment (the download path uses exactly one per experiment).
    """
    inventory_csv_url = (
        INVENTORY_DATA_REMOTE_URL if remote else INVENTORY_DATA_LOCAL_PATH
    )
    data = _read_inventory(inventory_csv_url)
    column_to_use = "location" if remote else "hub"
    activity_filter = "FAO" if dataset == "CORDEX-CORE" else "CRDX-ISIMIP-025"

    filtered_data = data[
        (data["activity"].str.contains(activity_filter, na=False))
        & (data["domain"] == cordex_domain)
        & (data["model"].str.contains(gcm, na=False))
        & (data["rcm"].str.contains(rcm, na=False))
        & (data["experiment"].isin(experiments))
    ][["experiment", column_to_use]].copy()

    _ensure_inventory_not_empty(
        filtered_data,
        dataset=dataset,
        cordex_domain=cordex_domain,
        gcm=gcm,
        rcm=rcm,
        experiments=experiments,
        activity_filter=activity_filter,
        log=log,
    )

    experiment_counts = filtered_data["experiment"].value_counts()
    ambiguous = experiment_counts[experiment_counts > 1]
    if not ambiguous.empty:
        raise ValueError(
            f"Ambiguous inventory match for domain={cordex_domain}, gcm={gcm}, "
            f"rcm={rcm}: multiple datasets found for experiment(s) "
            f"{sorted(ambiguous.index)}. Please report this at "
            "https://github.com/un-fao/cavapy/issues"
        )

    return filtered_data, column_to_use


def _validate_urls(
    gcm: str = None,
    rcm: str = None,
    rcp: str = None,
    remote: bool = True,
    cordex_domain: str = None,
    obs: bool = False,
    historical: bool = False,
    bias_correction: bool = False,
    dataset: str = "CORDEX-CORE",
    variables: list[str] | None = None,
):
    """Validate inventory availability and log resolved dataset URLs."""
    # Load the data
    log = logger.getChild("URL-validation")

    if obs is False:
        # Define which experiments we need
        experiments = [rcp]
        if historical or bias_correction:
            experiments.append("historical")

        filtered_data, column_to_use = _filter_inventory(
            remote=remote,
            dataset=dataset,
            cordex_domain=cordex_domain,
            gcm=gcm,
            rcm=rcm,
            experiments=experiments,
            log=log,
        )

        # Extract the column values as a list
        for _, row in filtered_data.iterrows():
            if row["experiment"] == "historical":
                log_hist = logger.getChild(f"URL-validation-{gcm}-{rcm}-historical")
                log_hist.info(f"{row[column_to_use]}")
            else:
                log_proj = logger.getChild(f"URL-validation-{gcm}-{rcm}-{rcp}")
                log_proj.info(f"{row[column_to_use]}")

    else:  # when obs is True
        if variables:
            for variable in variables:
                log_obs = logger.getChild(f"URL-validation-ERA5-{variable}")
                log_obs.info(f"{ERA5_DATA_REMOTE_URL}")
        else:
            log_obs = logger.getChild("URL-validation-ERA5")
            log_obs.info(f"{ERA5_DATA_REMOTE_URL}")


def _get_country_bounds(country_name: str) -> tuple[float, float, float, float]:
    """
    Get country bounding box using cartopy's Natural Earth data.

    Args:
        country_name: Name of the country

    Returns:
        tuple: (minx, miny, maxx, maxy) bounding box

    Raises:
        ValueError: If country not found
    """
    # Use Natural Earth countries dataset via cartopy
    countries_feature = cfeature.NaturalEarthFeature(
        "cultural", "admin_0_countries", "50m"
    )

    # Get the actual shapefile path from the feature
    _ = countries_feature.with_scale("50m").geometries()

    # Search for the country using Natural Earth records
    for country_record in shpreader.Reader(
        shpreader.natural_earth(
            resolution="50m", category="cultural", name="admin_0_countries"
        )
    ).records():
        # Try multiple name fields for better matching
        country_names = [
            country_record.attributes.get("NAME", ""),
            country_record.attributes.get("NAME_LONG", ""),
            country_record.attributes.get("ADMIN", ""),
            country_record.attributes.get("NAME_EN", ""),
        ]

        if any(name.lower() == country_name.lower() for name in country_names if name):
            return country_record.geometry.bounds

    # If not found, check for capitalization issue
    if country_name and country_name[0].islower():
        capitalized = country_name.capitalize()
        raise ValueError(
            f"Country '{country_name}' not found. Try capitalizing the first letter: '{capitalized}'"
        )
    else:
        raise ValueError(f"Country '{country_name}' is unknown.")


def _geo_localize(
    country: str = None,
    xlim: tuple[float, float] = None,
    ylim: tuple[float, float] = None,
    buffer: int = 0,
    cordex_domain: str = None,
    obs: bool = False,
) -> dict[str, tuple[float, float]]:
    """Resolve a country name or bbox into a validated bounding box."""
    if country:
        if xlim or ylim:
            raise ValueError(
                "Specify either a country or bounding box limits (xlim, ylim), but not both."
            )

        bounds = _get_country_bounds(country)
        xlim, ylim = (bounds[0], bounds[2]), (bounds[1], bounds[3])
    elif not (xlim and ylim):
        raise ValueError(
            "Either a country or bounding box limits (xlim, ylim) must be specified."
        )

    # Apply buffer
    xlim = (xlim[0] - buffer, xlim[1] + buffer)
    ylim = (ylim[0] - buffer, ylim[1] + buffer)

    # Only validate CORDEX domain when processing non-observational data
    # Skip validation for observations or when using dummy values
    if not obs and cordex_domain:
        _validate_cordex_domain(xlim, ylim, cordex_domain)

    return {"xlim": xlim, "ylim": ylim}


def _validate_gcm_rcm_combinations(cordex_domain: str, gcm: str, rcm: str):
    """
    Validate that the GCM-RCM combination is available for the specified CORDEX domain.

    Args:
        cordex_domain: CORDEX domain name
        gcm: Global Climate Model name
        rcm: Regional Climate Model name

    Raises:
        ValueError: If the combination is not available for the domain
    """
    # Define invalid combinations per domain
    invalid_combinations = {
        "WAS-22": [
            ("MOHC", "Reg")  # MOHC-Reg is not available for WAS-22
        ],
        "CAS-22": [
            ("MOHC", "Reg"),  # Reg is not available for any GCM in CAS-22
            ("MPI", "Reg"),
            ("NCC", "Reg"),
        ],
        "EUR-22": [
            ("MOHC", "Reg"),  # Only REMO runs exist for EUR-22
            ("MPI", "Reg"),
            ("NCC", "Reg"),
        ],
        "NAM-22": [
            ("MOHC", "Reg"),  # Only REMO runs exist for NAM-22
            ("MPI", "Reg"),
            ("NCC", "Reg"),
        ],
        "CAM-22": [
            ("NCC", "Reg"),  # CAM-22 pairs RegCM4-7 with NOAA-GFDL, not NorESM
        ],
    }

    if cordex_domain in invalid_combinations:
        invalid_combos = invalid_combinations[cordex_domain]
        current_combo = (gcm, rcm)

        if current_combo in invalid_combos:
            # Get available combinations for this domain
            all_gcm = VALID_GCM
            all_rcm = VALID_RCM
            available_combos = []

            for g in all_gcm:
                for r in all_rcm:
                    if (g, r) not in invalid_combos:
                        available_combos.append(f"{g}-{r}")

            raise ValueError(
                f"The combination {gcm}-{rcm} is not available for domain {cordex_domain}. "
                f"Available combinations for {cordex_domain}: {', '.join(available_combos)}"
            )


# Geographic extents (min_lon, min_lat, max_lon, max_lat) of the regridded
# 0.25-degree products served on THREDDS, measured from the datasets themselves
# (August 2026). No served domain crosses the antimeridian: AUS-22 and EAS-22
# are clipped at 180 degrees East.
CORDEX_DOMAIN_EXTENTS = {
    "NAM-22": (-171.75, 12.25, -22.25, 76.25),
    "EUR-22": (-44.75, 22.00, 65.00, 72.50),
    "SEA-22": (89.25, -15.25, 147.00, 26.50),
    "AUS-22": (86.25, -53.25, 180.00, 12.75),
    "WAS-22": (19.25, -15.75, 116.25, 45.75),
    "EAS-22": (44.75, 0.25, 179.75, 62.25),
    "SAM-22": (-106.25, -58.25, -16.25, 18.75),
    "CAM-22": (-124.75, -19.75, -21.75, 35.25),
    "AFR-22": (-24.25, -46.25, 59.75, 42.75),
    "CAS-22": (10.75, 17.75, 140.25, 69.75),
}


def _validate_cordex_domain(xlim, ylim, cordex_domain):
    """Ensure the bbox is fully contained inside the selected CORDEX domain."""
    if cordex_domain not in CORDEX_DOMAIN_EXTENTS:
        raise ValueError(f"CORDEX domain '{cordex_domain}' is not recognized.")

    def is_bbox_contained(bbox, extent):
        min_lon, min_lat, max_lon, max_lat = extent
        return (
            bbox[0] >= min_lon
            and bbox[1] >= min_lat
            and bbox[2] <= max_lon
            and bbox[3] <= max_lat
        )

    user_bbox = [xlim[0], ylim[0], xlim[1], ylim[1]]

    if is_bbox_contained(user_bbox, CORDEX_DOMAIN_EXTENTS[cordex_domain]):
        return

    suggested_domains = [
        domain
        for domain, extent in CORDEX_DOMAIN_EXTENTS.items()
        if is_bbox_contained(user_bbox, extent)
    ]

    if not suggested_domains:
        raise ValueError(
            f"The bounding box {user_bbox} is outside of all available CORDEX domains."
        )

    raise ValueError(
        f"Bounding box {user_bbox} is not within '{cordex_domain}'. Suggested domain: '{suggested_domains[0]}'."
    )
