"""Monitor circuit status and display real-time updates."""

# This script monitors active circuits and displays their status in real-time.
# Useful for understanding circuit behavior and debugging.

import time

# Configuration
UPDATE_INTERVAL = 5  # seconds
DURATION = 60  # Run for 60 seconds total

ctx.log("Circuit Monitoring Script")
ctx.log(f"Monitoring for {DURATION} seconds (updates every {UPDATE_INTERVAL}s)")
ctx.log("=" * 70)

iterations = DURATION // UPDATE_INTERVAL
for i in range(iterations):
    circuits = tor.list_circuits()

    ctx.log(f"\n[{i+1}/{iterations}] Active Circuits: {len(circuits)}")
    ctx.log("-" * 70)

    if not circuits:
        ctx.log("  No active circuits")
    else:
        # Group by status
        by_status = {}
        for circuit in circuits:
            status = circuit.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(circuit)

        # Display grouped circuits
        for status, status_circuits in sorted(by_status.items()):
            ctx.log(f"\n  {status} ({len(status_circuits)}):")
            for circuit in status_circuits[:3]:  # Show first 3
                age_min = circuit.age_seconds // 60
                age_sec = circuit.age_seconds % 60
                path_preview = " -> ".join(hop.nickname for hop in circuit.path[:2])
                if len(circuit.path) > 2:
                    path_preview += " -> ..."

                ctx.log(
                    f"    Circuit {circuit.id}: {age_min}m{age_sec}s old - {path_preview}"
                )

            if len(status_circuits) > 3:
                ctx.log(f"    ... and {len(status_circuits) - 3} more")

    # Sleep unless last iteration
    if i < iterations - 1:
        time.sleep(UPDATE_INTERVAL)

ctx.log("\n" + "=" * 70)
ctx.log("Monitoring complete!")
