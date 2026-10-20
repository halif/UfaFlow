# Changelog

All notable changes to this project will be documented in this file.

## [1.0.6] - 2026-10-20

### Added
- CLI config validation for missing and malformed frontend/backend settings
- Clearer startup error messages for invalid YAML and missing config files
- Smoke tests covering package version exposure, config validation, and CLI help output

### Changed
- Improved release readiness by tightening CLI validation and user-facing diagnostics
- Clarified project stability and configuration expectations for local setup and packaging

## [1.0.5] - 2026-10-19

### Fixed
- Fixed package installation and import behavior for `ufaflow`
- Fixed missing `__version__` export from the package
- Corrected package initialization issue caused by invalid `___init___.py` filename
- Verified CLI entry point works correctly via `python -m ufaflow.cli --help`

### Changed
- Standardized package metadata and build configuration
- Cleaned up release configuration for the wheel and source distribution

### Added
- Release version metadata for the package
- Basic changelog for tracking future updates
