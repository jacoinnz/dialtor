"""Demonstrate creating and managing onion services."""

# This script shows how to create ephemeral onion services programmatically.
# Useful for quickly exposing local services over Tor.

import time

ctx.log("Onion Service Demo Script")
ctx.log("=" * 50)

# Create onion service for local web server
ctx.log("\nCreating onion service...")
ctx.log("  Virtual port: 80")
ctx.log("  Target: 127.0.0.1:8080")

try:
    service = tor.create_onion_service(
        virtual_port=80,
        target_port=8080,
        target_address="127.0.0.1",
    )

    ctx.log(f"\n✓ Onion service created!")
    ctx.log(f"  Address: {service.onion_address}")
    ctx.log(f"  Service ID: {service.service_id}")

    if service.key_content:
        ctx.log(f"\n  Private key: {service.key_content[:32]}...")
        ctx.log("  (Save this key to recreate the same address later)")

    ctx.log(f"\nYour service is now accessible at:")
    ctx.log(f"  http://{service.onion_address}")

    # List all services
    ctx.log("\nListing all active onion services...")
    services = tor.list_onion_services()
    ctx.log(f"  Total services: {len(services)}")

    for svc in services:
        ctx.log(f"    - {svc.onion_address}")

    # Keep service alive for a bit
    ctx.log("\nService will remain active for 30 seconds...")
    ctx.log("(Press Ctrl+C to stop early)")

    try:
        time.sleep(30)
    except KeyboardInterrupt:
        ctx.log("\nInterrupted by user")

    # Remove service
    ctx.log("\nRemoving onion service...")
    tor.remove_onion_service(service.service_id)
    ctx.log("✓ Service removed")

except Exception as e:
    ctx.error(f"Error: {e}")

ctx.log("\n" + "=" * 50)
ctx.log("Demo complete!")
