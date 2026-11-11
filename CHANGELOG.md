# Changelog

All notable changes to this project are documented in this file.

## [2.1.5] - 2026-11-11

### Fixed
- `import cavapy` failed with `ModuleNotFoundError: No module named 'xclim.indices'`
  on fresh installs. xclim 1.0 renamed `xclim.indices` to `xclim.compute`, but
  xsdba (0.7.0) still imports from `xclim.indices`. xclim is now constrained to
  `>=0.56,<1.0` until xsdba supports xclim 1.0.
