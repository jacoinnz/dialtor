"""Create circuits through specific countries."""

# This script demonstrates creating circuits with exit nodes in specific countries.
# Useful for testing geolocation or accessing country-specific content.

COUNTRIES = ["US", "DE", "NL", "FR", "GB"]

ctx.log("Creating circuits with country-specific exits...")

created_circuits = []

for country in COUNTRIES:
    try:
        ctx.log(f"\nCreating circuit with {country} exit...")

        # Create circuit with specific exit country
        circuit = tor.create_circuit(exit_country=country)

        ctx.log(f"  ✓ Circuit {circuit.id} created")
        ctx.log(f"  Path: {circuit.path_string}")

        created_circuits.append((country, circuit))

    except Exception as e:
        ctx.error(f"  ✗ Failed to create {country} circuit: {e}")

ctx.log(f"\n✓ Successfully created {len(created_circuits)} circuits")

# Display summary
if created_circuits:
    ctx.log("\nCircuit Summary:")
    for country, circuit in created_circuits:
        ctx.log(f"  {country}: Circuit {circuit.id} ({len(circuit.path)} hops)")
