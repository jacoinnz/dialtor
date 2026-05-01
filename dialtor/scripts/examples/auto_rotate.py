"""Automatically rotate circuits older than specified age."""

# This script automatically rotates (closes) circuits that are older than
# a specified age. This helps maintain fresh circuits for better anonymity.

import time

# Configuration
MAX_CIRCUIT_AGE = 300  # 5 minutes in seconds
CHECK_INTERVAL = 60  # Check every 60 seconds
MAX_ITERATIONS = 10  # Run for 10 iterations then exit

ctx.log(f"Auto-rotation script started")
ctx.log(f"  Max circuit age: {MAX_CIRCUIT_AGE} seconds")
ctx.log(f"  Check interval: {CHECK_INTERVAL} seconds")

for iteration in range(MAX_ITERATIONS):
    ctx.log(f"\nIteration {iteration + 1}/{MAX_ITERATIONS}")

    # Get all circuits
    circuits = tor.list_circuits()
    ctx.log(f"  Active circuits: {len(circuits)}")

    # Find old circuits
    old_circuits = [c for c in circuits if c.age_seconds > MAX_CIRCUIT_AGE]

    if old_circuits:
        ctx.log(f"  Found {len(old_circuits)} old circuits to close")

        for circuit in old_circuits:
            try:
                tor.close_circuit(circuit.id)
                ctx.log(f"    Closed circuit {circuit.id} (age: {circuit.age_seconds}s)")
            except Exception as e:
                ctx.error(f"    Failed to close circuit {circuit.id}: {e}")
    else:
        ctx.log("  No old circuits to close")

    # Sleep unless last iteration
    if iteration < MAX_ITERATIONS - 1:
        ctx.log(f"  Sleeping for {CHECK_INTERVAL} seconds...")
        time.sleep(CHECK_INTERVAL)

ctx.log("\nAuto-rotation script finished")
