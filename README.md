# dialtor

**Advanced Tor network control CLI**

Professional command-line tool for managing Tor network connections, circuits, and relays. Control your Tor circuits, rotate identity, select specific exit nodes, and more.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Connection Management**: Connect to Tor network and verify status
- **Circuit Control**: Create, list, and close custom circuits
- **Identity Management**: Request new identity and rotate old circuits
- **Relay Selection**: Filter and select relays by country, flags, and bandwidth *(coming soon)*
- **Bridge Support**: Configure bridges for censorship circumvention *(coming soon)*
- **Onion Services**: Manage hidden services *(coming soon)*
- **Python Scripting**: Automate Tor control with Python scripts *(coming soon)*

## Installation

### Prerequisites

- Python 3.10 or higher
- Tor daemon installed and running
- Access to Tor control port (default: 9051)

### Install Tor

**macOS:**
```bash
brew install tor
brew services start tor
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tor
sudo systemctl start tor
```

**Arch Linux:**
```bash
sudo pacman -S tor
sudo systemctl start tor
```

### Install dialtor

#### From source (current):

```bash
# Clone the repository
git clone https://github.com/jacoinnz/dialtor.git
cd dialtor

# Install with Poetry
poetry install

# Or install with pip
pip install -e .
```

#### From PyPI *(coming soon)*:

```bash
pip install dialtor
```

## Quick Start

### 1. Verify Tor Connection

```bash
dialtor connect verify
```

This connects to your local Tor daemon and displays connection status, version, and active circuits.

### 2. List Active Circuits

```bash
dialtor circuit list
```

Shows all active Tor circuits with their status, paths (relay hops), and age.

### 3. Create a New Circuit

```bash
# Create a basic circuit (3 hops)
dialtor circuit create

# Create circuit with specific exit country
dialtor circuit create --exit-country US

# Create circuit with custom number of hops
dialtor circuit create --hops 4
```

### 4. Request New Identity

```bash
dialtor identity new
```

Sends NEWNYM signal to Tor for a fresh identity. Subsequent connections will use new circuits.

### 5. Rotate Old Circuits

```bash
# Close circuits older than 10 minutes (600 seconds)
dialtor identity rotate --max-age 600
```

## Configuration

dialtor looks for configuration files in the following locations (in order):

1. `~/.dialtor/config.toml`
2. `~/.config/dialtor/config.toml`
3. `/etc/dialtor/config.toml`

### Example Configuration

Create `~/.dialtor/config.toml`:

```toml
[connection]
control_port = 9051
# control_socket = "/var/run/tor/control"
password = "your_password_here"
timeout = 30

[relay_selection]
preferred_countries = ["us", "de", "nl"]
min_bandwidth = 1048576  # 1 MB/s
required_flags = ["Fast", "Stable"]

[logging]
level = "INFO"
# file = "~/.dialtor/dialtor.log"
```

### Environment Variables

Override configuration with environment variables:

```bash
export DIALTOR_CONTROL_PORT=9051
export DIALTOR_PASSWORD="your_password"
export DIALTOR_LOG_LEVEL="DEBUG"

dialtor connect verify
```

## Command Reference

### Connect Commands

```bash
# Verify connection to Tor
dialtor connect verify

# Use custom port
dialtor connect verify --port 9052

# Provide password
dialtor connect verify --password "secret"
```

### Circuit Commands

```bash
# List all circuits
dialtor circuit list

# Create new circuit
dialtor circuit create

# Create circuit with exit in Germany
dialtor circuit create --exit-country DE

# Show circuit details
dialtor circuit info <circuit-id>

# Close a circuit
dialtor circuit close <circuit-id>
```

### Identity Commands

```bash
# Request new identity (NEWNYM)
dialtor identity new

# Rotate circuits older than 5 minutes
dialtor identity rotate --max-age 300

# Show identity status
dialtor identity status
```

## Troubleshooting

### Tor daemon not running

```
Error: Tor daemon is not running or not accessible on port 9051
```

**Solution**: Start the Tor daemon:
```bash
# macOS
brew services start tor

# Linux
sudo systemctl start tor
```

### Authentication failed

```
Authentication Error: Failed to authenticate with Tor
```

**Solution**: Check your Tor control port password. Set it in the config file or via environment variable:

```bash
export DIALTOR_PASSWORD="your_password"
```

### Connection refused

```
Error: Connection refused
```

**Solution**: Verify Tor control port is enabled. Edit `/etc/tor/torrc` (or `/usr/local/etc/tor/torrc` on macOS):

```
ControlPort 9051
CookieAuthentication 1
```

Then restart Tor.

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/jacoinnz/dialtor.git
cd dialtor

# Install with development dependencies
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov

# Type checking
poetry run mypy dialtor

# Linting
poetry run ruff check dialtor

# Format code
poetry run black dialtor
```

### Running Tests

```bash
# Unit tests only (no Tor required)
poetry run pytest tests/unit

# Integration tests (Tor required)
poetry run pytest tests/integration

# All tests with coverage
poetry run pytest -v --cov=dialtor --cov-report=html
```

## Roadmap

- [x] Phase 1: Core Foundation (MVP)
  - [x] Project setup and structure
  - [x] Tor connection and authentication
  - [x] Basic circuit management
  - [x] Identity rotation
- [ ] Phase 2: Advanced Relay Selection
  - [ ] Relay filtering by country, flags, bandwidth
  - [ ] Custom relay selection for circuits
  - [ ] Interactive relay browser
- [ ] Phase 3: Bridge and Onion Services
  - [ ] Bridge configuration
  - [ ] Onion service management
- [ ] Phase 4: Scripting Support
  - [ ] Python scripting API
  - [ ] Example automation scripts
- [ ] Phase 5: Polish
  - [ ] Shell completion
  - [ ] Man pages
  - [ ] PyPI release

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/) (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Security

dialtor is a tool for controlling Tor circuits. Use it responsibly and ethically.

- Never log control port passwords in plain text
- Be cautious when scripting Tor operations
- Review the [Tor Project documentation](https://www.torproject.org/) for best practices

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [stem](https://stem.torproject.org/) - Python library for Tor
- CLI powered by [Typer](https://typer.tiangolo.com/)
- Beautiful output with [Rich](https://rich.readthedocs.io/)
- Thanks to the [Tor Project](https://www.torproject.org/) for their work on privacy and anonymity

## Links

- **Repository**: https://github.com/jacoinnz/dialtor
- **Issue Tracker**: https://github.com/jacoinnz/dialtor/issues
- **Tor Project**: https://www.torproject.org/
- **stem Documentation**: https://stem.torproject.org/

---

Made with by dialtor contributors
