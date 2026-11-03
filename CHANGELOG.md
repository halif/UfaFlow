# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.0.8] - 2026-11-03

### Added
- Added multi-worker support on Unix-like systems by sharing listening sockets with worker processes through Python multiprocessing.
- Added an end-to-end test for multi-worker traffic proxying and clean shutdown.

### Changed
- Explicitly reject `--workers > 1` on Windows; Windows remains supported in single-process mode.

### Documentation
- Updated the README with current PyPI installation and CLI usage instructions.
- Added configuration and troubleshooting guides and updated the example `config.yaml`.
- Clarified platform-specific support for single-process and multi-worker modes.

## [1.0.7] - 2026-10-21

### Added
- Added `ufaflow status <config.yaml>` for runtime health reporting
- Added structured JSON status output for frontend/backend health checks

### Improved
- Improved worker startup diagnostics and process lifecycle logging
- Improved config validation errors with frontend/backend context
- Improved backend availability warnings for faster troubleshooting
- Improved operational visibility without altering core load-balancing behavior

### Tests
- Added CLI smoke coverage for status reporting and validation scenarios
- Added failure-visibility checks for invalid config and degraded backend states

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
