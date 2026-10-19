# Changelog

All notable changes to this project will be documented in this file.

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