"""Discover and analyze Tor relays by region."""

# This script analyzes the Tor network by discovering relays in different regions
# and displaying statistics about their capabilities.

from collections import defaultdict

ctx.log("Tor Relay Discovery Script")
ctx.log("=" * 50)

# Fetch all relays
ctx.log("\nFetching relay consensus...")
all_relays = tor.list_relays()
ctx.log(f"Total relays: {len(all_relays)}")

# Analyze by country
country_counts = defaultdict(int)
for relay in all_relays:
    if relay.country_code:
        country_counts[relay.country_code] += 1

# Top countries
ctx.log("\nTop 10 Countries by Relay Count:")
for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    percentage = (count / len(all_relays)) * 100
    ctx.log(f"  {country}: {count} relays ({percentage:.1f}%)")

# Analyze by flags
ctx.log("\nRelay Capabilities:")

fast_relays = [r for r in all_relays if "Fast" in r.flags]
ctx.log(f"  Fast:   {len(fast_relays)} ({len(fast_relays)/len(all_relays)*100:.1f}%)")

stable_relays = [r for r in all_relays if "Stable" in r.flags]
ctx.log(f"  Stable: {len(stable_relays)} ({len(stable_relays)/len(all_relays)*100:.1f}%)")

guard_relays = [r for r in all_relays if "Guard" in r.flags]
ctx.log(f"  Guard:  {len(guard_relays)} ({len(guard_relays)/len(all_relays)*100:.1f}%)")

exit_relays = [r for r in all_relays if "Exit" in r.flags]
ctx.log(f"  Exit:   {len(exit_relays)} ({len(exit_relays)/len(all_relays)*100:.1f}%)")

# Bandwidth analysis
ctx.log("\nBandwidth Distribution:")
bandwidth_ranges = {
    "> 100 MB/s": len([r for r in all_relays if r.bandwidth >= 104_857_600]),
    "> 10 MB/s": len([r for r in all_relays if r.bandwidth >= 10_485_760]),
    "> 1 MB/s": len([r for r in all_relays if r.bandwidth >= 1_048_576]),
    "< 1 MB/s": len([r for r in all_relays if r.bandwidth < 1_048_576]),
}

for range_name, count in bandwidth_ranges.items():
    percentage = (count / len(all_relays)) * 100
    ctx.log(f"  {range_name}: {count} relays ({percentage:.1f}%)")

# Find high-quality relays
ctx.log("\nTop 5 High-Bandwidth Relays:")
top_relays = sorted(all_relays, key=lambda r: r.bandwidth, reverse=True)[:5]
for i, relay in enumerate(top_relays, 1):
    bw_mbps = relay.bandwidth / 1_048_576
    ctx.log(
        f"  {i}. {relay.nickname} ({relay.country_code or '??'}): "
        f"{bw_mbps:.1f} MB/s - {', '.join(sorted(relay.flags))}"
    )

ctx.log("\n" + "=" * 50)
ctx.log("Relay discovery complete!")
