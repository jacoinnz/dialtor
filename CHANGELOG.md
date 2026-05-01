# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Shell completion support for bash, zsh, and fish
- Manual pages (man dialtor)
- PyPI package preparation

## [0.1.0] - 2026-05-01

### Added
- **Phase 1: Core Foundation (MVP)**
  - Tor connection and authentication via control port
  - Circuit management (list, create, close, info)
  - Identity rotation (new identity, rotate old circuits)
  - Configuration file support (TOML format)
  - Environment variable overrides
  - Error handling with user-friendly messages
  - Rich terminal output formatting

- **Phase 2: Advanced Relay Selection**
  - Relay filtering by country code
  - Relay filtering by flags (Fast, Stable, Guard, Exit, etc.)
  - Relay filtering by minimum bandwidth
  - Random relay selection from filtered set
  - Circuit creation with specific exit country
  - Circuit creation with custom relay path
  - Relay information display (detailed and list views)

- **Phase 3: Bridge and Onion Services**
  - Bridge configuration management
  - Support for multiple bridge types (vanilla, obfs4, meek, snowflake, webtunnel)
  - Bridge connectivity testing
  - Ephemeral v3 onion service creation
  - Onion service lifecycle management
  - Onion service key management

- **Phase 4: Python Scripting API**
  - Complete Python API for programmatic control
  - Context manager support for automatic cleanup
  - Script runner with context injection
  - Five example automation scripts:
    - auto_rotate.py - Automatic circuit rotation
    - country_routing.py - Multi-country circuit creation
    - relay_discovery.py - Relay analysis by country
    - onion_automation.py - Onion service automation
    - bridge_manager.py - Bridge configuration management
  - Comprehensive API documentation (docs/API.md)

- **Phase 5: Polish**
  - Shell completion for bash, zsh, and fish
  - Unix manual pages (man dialtor)
  - Makefile for man page installation
  - PyPI package preparation and metadata

### Features
- 22 CLI commands across 7 command groups
- 40 unit tests with 100% pass rate
- Full type hints and mypy compliance
- Pydantic data models for type safety
- TDD development approach
- Conventional Commits for version control

### Documentation
- Comprehensive README with examples
- API documentation for Python library usage
- Man pages for Unix systems
- Example automation scripts
- Configuration guide
- Troubleshooting section

## Release Types

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Pre-release Identifiers

- **alpha**: Early testing (0.1.0-alpha.1)
- **beta**: Feature complete, testing (0.1.0-beta.1)
- **rc**: Release candidate (0.1.0-rc.1)

[Unreleased]: https://github.com/jacoinnz/dialtor/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jacoinnz/dialtor/releases/tag/v0.1.0
