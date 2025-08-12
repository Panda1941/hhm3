import os
import re
from collections import defaultdict

# Set the path to your HOI4 mod or game state files
STATE_FILES_DIR = "history/states"

# Regex patterns
owner_pattern = re.compile(r"owner\s*=\s*(\w+)")
buildings_block_pattern = re.compile(r"buildings\s*=\s*\{([^}]+)\}")
factory_pattern = re.compile(r"(industrial_complex|arms_factory|dockyard|naval_dockyard)\s*=\s*(\d+)")

# Aggregated results: { tag: { factory_type: count } }
country_factories = defaultdict(lambda: defaultdict(int))

# Tags to completely ignore from processing
IGNORED_TAGS = {
    "WST", "SWE", "FIN"
}

simulate_annexations = True
SIMULATED_ANNEXATIONS = {
    "ENG": ["IRE"],
    "JAP": ["MAN", "SIA"],
    "ITA": ["ETH"],
}

simulate_no_asia = True
NO_ASIA_TAGS = {
    "CHI", "MAN", "JAP", "RAJ", "PHI", "AST", "NZL", "MEX", "USA"
}

FACTIONS = {
    "Axis": {"GER", "ITA", "HUN", "ROM", "BUL", "SPR"},
    "Allies": {"ENG", "FRA", "CAN", "SAF", "BRA", "USA"},
    "Comintern": {"SOV"},
    "Co-Prosperity" : {"JAP"},
}

# Process each state file
for filename in os.listdir(STATE_FILES_DIR):
    if not filename.endswith(".txt"):
        continue

    with open(os.path.join(STATE_FILES_DIR, filename), "r", encoding="utf-8") as f:
        content = f.read()

        # Extract country tag
        owner_match = owner_pattern.search(content)
        if not owner_match:
            continue
        tag = owner_match.group(1)
        
        if tag in IGNORED_TAGS:
            continue

        # Extract buildings block
        buildings_match = buildings_block_pattern.search(content)
        if not buildings_match:
            continue
        buildings_block = buildings_match.group(1)

        # Extract factory counts
        for factory_type, count in factory_pattern.findall(buildings_block):
            normalized_type = (
                "dockyard" if factory_type == "naval_dockyard" else factory_type
            )
            country_factories[tag][normalized_type] += int(count)

if simulate_annexations:
    for annexer, annexed_list in SIMULATED_ANNEXATIONS.items():
        if annexer in IGNORED_TAGS:
            continue
        for annexed in annexed_list:
            if annexed in IGNORED_TAGS:
                continue
            if annexed not in country_factories:
                continue
            for factory_type, count in country_factories[annexed].items():
                country_factories[annexer][factory_type] += count
            del country_factories[annexed]

if simulate_no_asia:
    for tag in NO_ASIA_TAGS:
        if tag in country_factories:
            del country_factories[tag]

# Print results
for tag, factories in sorted(country_factories.items()):
    civs = factories.get("industrial_complex", 0)
    mils = factories.get("arms_factory", 0)
    docks = factories.get("dockyard", 0)
    print(f"{tag}: Civs={civs}, Mils={mils}, Docks={docks}")

# Faction summary: {faction: {factory_type: total}}
faction_factories = defaultdict(lambda: defaultdict(int))

for faction, members in FACTIONS.items():
    for tag in members:
        if tag in IGNORED_TAGS:
            continue
        if tag not in country_factories:
            continue
        for factory_type, count in country_factories[tag].items():
            faction_factories[faction][factory_type] += count

print("\n=== Faction Totals ===")
for faction, factories in faction_factories.items():
    civs = factories.get("industrial_complex", 0)
    mils = factories.get("arms_factory", 0)
    docks = factories.get("dockyard", 0)
    print(f"{faction}: Civs={civs}, Mils={mils}, Docks={docks}")
