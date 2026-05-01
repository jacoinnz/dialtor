# dialtor Python API Documentation

The dialtor Python API allows you to control Tor programmatically from your Python scripts.

## Installation

```bash
pip install -e .  # Install from source
# or when published:
# pip install dialtor
```

## Quick Start

```python
from dialtor.api import Dialtor

# Create and connect
tor = Dialtor()
tor.connect()

# Create a circuit with US exit
circuit = tor.create_circuit(exit_country="US")
print(f"Created circuit: {circuit.id}")

# Get US relays
relays = tor.list_relays(country="US", flags=["Fast"], limit=10)
print(f"Found {len(relays)} fast US relays")

# Request new identity
tor.new_identity()

# Disconnect
tor.disconnect()
```

## Using Context Manager

```python
from dialtor.api import Dialtor

# Automatically connects and disconnects
with Dialtor() as tor:
    circuit = tor.create_circuit(exit_country="DE")
    print(f"Circuit: {circuit.path_string}")
```

## API Reference

### Dialtor Class

#### Initialization

```python
Dialtor(port=9051, password=None, config_file=None)
```

**Parameters:**
- `port` (int): Tor control port (default: 9051)
- `password` (str, optional): Control port password
- `config_file` (Path, optional): Path to configuration file

**Example:**
```python
tor = Dialtor(port=9052, password="secret")
```

#### Connection Methods

##### `connect()` → bool

Connect to Tor control port.

**Returns:** `True` if successful

**Raises:**
- `TorNotRunningError`: If Tor daemon not running
- `TorConnectionError`: If connection fails

**Example:**
```python
tor = Dialtor()
tor.connect()
```

##### `disconnect()` → None

Disconnect from Tor.

**Example:**
```python
tor.disconnect()
```

##### `is_connected()` → bool

Check if connected to Tor.

**Returns:** `True` if connected

**Example:**
```python
if tor.is_connected():
    print("Connected!")
```

### Circuit Methods

#### `list_circuits()` → List[Circuit]

List all active circuits.

**Returns:** List of `Circuit` objects

**Example:**
```python
circuits = tor.list_circuits()
for circuit in circuits:
    print(f"{circuit.id}: {circuit.path_string} ({circuit.age_seconds}s)")
```

#### `create_circuit(hops=3, exit_country=None, relays=None)` → Circuit

Create a new circuit.

**Parameters:**
- `hops` (int): Number of hops (default: 3)
- `exit_country` (str, optional): Exit node country code (e.g., "US", "DE")
- `relays` (List[str], optional): List of relay fingerprints for custom path

**Returns:** Created `Circuit` object

**Example:**
```python
# Basic circuit
circuit = tor.create_circuit()

# US exit
circuit = tor.create_circuit(exit_country="US")

# Custom path
circuit = tor.create_circuit(relays=["AAAA...", "BBBB...", "CCCC..."])
```

#### `close_circuit(circuit_id)` → bool

Close a specific circuit.

**Parameters:**
- `circuit_id` (str): Circuit ID to close

**Returns:** `True` if successful

**Example:**
```python
tor.close_circuit("12345")
```

#### `get_circuit(circuit_id)` → Optional[Circuit]

Get circuit information.

**Parameters:**
- `circuit_id` (str): Circuit ID

**Returns:** `Circuit` object or `None` if not found

**Example:**
```python
circuit = tor.get_circuit("12345")
if circuit:
    print(circuit.path_string)
```

### Relay Methods

#### `list_relays(country=None, flags=None, min_bandwidth=None, limit=None)` → List[Relay]

List and filter relays.

**Parameters:**
- `country` (str, optional): Country code filter (e.g., "US")
- `flags` (List[str], optional): Flags filter (e.g., `["Fast", "Stable"]`)
- `min_bandwidth` (int, optional): Minimum bandwidth in bytes/sec
- `limit` (int, optional): Maximum number of relays to return

**Returns:** List of `Relay` objects

**Example:**
```python
# All relays
all_relays = tor.list_relays()

# US relays only
us_relays = tor.list_relays(country="US")

# Fast and stable relays
fast_relays = tor.list_relays(flags=["Fast", "Stable"], min_bandwidth=5_000_000)

# Top 10 by bandwidth
top_10 = tor.list_relays(limit=10)
```

#### `get_relay(fingerprint)` → Optional[Relay]

Get relay information.

**Parameters:**
- `fingerprint` (str): Relay fingerprint (full or partial)

**Returns:** `Relay` object or `None` if not found

**Example:**
```python
relay = tor.get_relay("AAAA1111BBBB2222")
if relay:
    print(f"{relay.nickname}: {relay.bandwidth} bytes/s")
```

#### `select_random_relays(count=1, country=None, flags=None, min_bandwidth=None)` → List[Relay]

Select random relays matching criteria.

**Parameters:**
- `count` (int): Number of relays to select
- `country` (str, optional): Country filter
- `flags` (List[str], optional): Flags filter
- `min_bandwidth` (int, optional): Bandwidth filter

**Returns:** List of randomly selected relays

**Example:**
```python
# 3 random fast US relays
relays = tor.select_random_relays(
    count=3,
    country="US",
    flags=["Fast", "Stable"]
)
```

### Identity Methods

#### `new_identity()` → None

Request a new Tor identity (NEWNYM signal).

**Example:**
```python
tor.new_identity()
print("New identity requested")
```

#### `rotate_circuits(max_age=600)` → int

Close circuits older than specified age.

**Parameters:**
- `max_age` (int): Maximum circuit age in seconds (default: 600)

**Returns:** Number of circuits closed

**Example:**
```python
# Close circuits older than 5 minutes
closed = tor.rotate_circuits(max_age=300)
print(f"Closed {closed} old circuits")
```

### Bridge Methods

#### `add_bridge(bridge_line)` → Bridge

Add a bridge.

**Parameters:**
- `bridge_line` (str): Bridge configuration line

**Returns:** `Bridge` object

**Example:**
```python
bridge = tor.add_bridge("obfs4 192.0.2.1:9001 AAAA... cert=...,iat-mode=0")
print(f"Added bridge: {bridge}")
```

#### `remove_bridge(address, port)` → bool

Remove a bridge.

**Parameters:**
- `address` (str): Bridge address
- `port` (int): Bridge port

**Returns:** `True` if removed

**Example:**
```python
removed = tor.remove_bridge("192.0.2.1", 9001)
```

#### `list_bridges()` → List[Bridge]

List configured bridges.

**Returns:** List of `Bridge` objects

**Example:**
```python
bridges = tor.list_bridges()
for bridge in bridges:
    print(f"{bridge.address}:{bridge.port} ({bridge.transport})")
```

### Onion Service Methods

#### `create_onion_service(virtual_port, target_port, target_address="127.0.0.1")` → OnionService

Create an ephemeral onion service.

**Parameters:**
- `virtual_port` (int): Port advertised in .onion address
- `target_port` (int): Local port where service listens
- `target_address` (str): Local address (default: "127.0.0.1")

**Returns:** `OnionService` object

**Example:**
```python
# Expose local web server
service = tor.create_onion_service(virtual_port=80, target_port=8080)
print(f"Service: http://{service.onion_address}")
print(f"Private key: {service.key_content}")
```

#### `remove_onion_service(service_id)` → bool

Remove an onion service.

**Parameters:**
- `service_id` (str): Service ID or .onion address

**Returns:** `True` if removed

**Example:**
```python
tor.remove_onion_service("abc123def456.onion")
```

#### `list_onion_services()` → List[OnionService]

List active onion services.

**Returns:** List of `OnionService` objects

**Example:**
```python
services = tor.list_onion_services()
for service in services:
    print(service.onion_address)
```

### Utility Methods

#### `get_tor_version()` → str

Get Tor version.

**Returns:** Tor version string

**Example:**
```python
version = tor.get_tor_version()
print(f"Tor version: {version}")
```

## Data Models

### Circuit

```python
class Circuit:
    id: str                    # Circuit ID
    status: CircuitStatus      # BUILT, LAUNCHED, etc.
    path: List[CircuitPath]    # List of relay hops
    purpose: str               # Circuit purpose
    created_at: datetime       # Creation timestamp
    age_seconds: int           # Age in seconds (property)
    path_string: str           # Human-readable path (property)
```

### Relay

```python
class Relay:
    fingerprint: str           # Relay fingerprint
    nickname: str              # Relay nickname
    address: str               # IP address
    or_port: int               # OR port
    dir_port: int              # Directory port
    flags: Set[RelayFlags]     # Relay flags
    bandwidth: int             # Bandwidth in bytes/sec
    country_code: str          # Country code
```

### Bridge

```python
class Bridge:
    address: str               # Bridge address
    port: int                  # Bridge port
    fingerprint: str           # Bridge fingerprint
    transport: BridgeType      # Transport type
    transport_options: str     # Transport options
    bridge_line: str           # Config line (property)
```

### OnionService

```python
class OnionService:
    service_id: str            # Service ID
    virtual_port: int          # Advertised port
    target_port: int           # Local port
    target_address: str        # Local address
    key_content: str           # Private key
    onion_address: str         # Full .onion address (property)
```

## Complete Examples

### Example 1: Auto-Rotation Script

```python
from dialtor.api import Dialtor
import time

with Dialtor() as tor:
    print("Auto-rotation script started")

    for i in range(10):
        circuits = tor.list_circuits()
        old = [c for c in circuits if c.age_seconds > 300]

        for circuit in old:
            tor.close_circuit(circuit.id)
            print(f"Closed old circuit: {circuit.id}")

        time.sleep(60)
```

### Example 2: Country-Specific Routing

```python
from dialtor.api import Dialtor

countries = ["US", "DE", "NL", "FR", "GB"]

with Dialtor() as tor:
    for country in countries:
        circuit = tor.create_circuit(exit_country=country)
        print(f"{country}: {circuit.path_string}")
```

### Example 3: Relay Discovery

```python
from dialtor.api import Dialtor

with Dialtor() as tor:
    # Get all fast, stable relays
    relays = tor.list_relays(
        flags=["Fast", "Stable"],
        min_bandwidth=10_000_000  # 10 MB/s
    )

    # Analyze by country
    by_country = {}
    for relay in relays:
        country = relay.country_code or "Unknown"
        by_country[country] = by_country.get(country, 0) + 1

    # Top countries
    for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{country}: {count} relays")
```

### Example 4: Onion Service Automation

```python
from dialtor.api import Dialtor
import time

with Dialtor() as tor:
    # Create onion service
    service = tor.create_onion_service(
        virtual_port=80,
        target_port=8080
    )

    print(f"Service created: http://{service.onion_address}")
    print(f"Private key: {service.key_content}")

    # Keep alive for 5 minutes
    time.sleep(300)

    # Service will be automatically removed on exit
```

## Error Handling

All API methods raise appropriate exceptions:

```python
from dialtor.api import Dialtor
from dialtor.utils.exceptions import (
    TorNotRunningError,
    TorConnectionError,
    CircuitCreationError,
)

try:
    tor = Dialtor()
    tor.connect()
    circuit = tor.create_circuit(exit_country="US")
except TorNotRunningError:
    print("Tor daemon is not running")
except TorConnectionError as e:
    print(f"Connection failed: {e}")
except CircuitCreationError as e:
    print(f"Failed to create circuit: {e}")
finally:
    if tor.is_connected():
        tor.disconnect()
```

## Best Practices

1. **Always use context manager** for automatic cleanup:
   ```python
   with Dialtor() as tor:
       # Your code here
   # Automatically disconnected
   ```

2. **Handle exceptions** appropriately:
   ```python
   try:
       tor.new_identity()
   except Exception as e:
       print(f"Error: {e}")
   ```

3. **Close old circuits** periodically:
   ```python
   tor.rotate_circuits(max_age=600)
   ```

4. **Use filters** to find suitable relays:
   ```python
   relays = tor.list_relays(
       country="US",
       flags=["Fast", "Stable"],
       min_bandwidth=5_000_000
   )
   ```

5. **Save onion service keys** for persistence:
   ```python
   service = tor.create_onion_service(80, 8080)
   with open("onion_key.txt", "w") as f:
       f.write(service.key_content)
   ```
