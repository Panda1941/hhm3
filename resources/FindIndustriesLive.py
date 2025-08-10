import os
import re
from collections import defaultdict
import matplotlib.pyplot as plt

SAVE_DIR = "C:/Users/pauli/Documents/Paradox Interactive/Hearts of Iron IV/save games"
FILE_SUFFIX = ".hoi4"

date_pattern = re.compile(r'^date\s*=\s*"?([\d\.]+)"?')
owner_pattern = re.compile(r'\bowner\s*=\s*"?(\w+)"?')

building_types = {"industrial_complex", "arms_factory", "dockyard", "naval_dockyard"}

timeline_data = defaultdict(lambda: defaultdict(lambda: {"civs": 0, "mils": 0, "docks": 0}))

def extract_brace_block(lines, start_index):
    """
    Extract a block starting at lines[start_index] that starts with {...}
    Returns the block as list of lines and the index of last line of block.
    """
    block_lines = []
    brace_level = 0
    for i in range(start_index, len(lines)):
        line = lines[i]
        brace_level += line.count('{') - line.count('}')
        block_lines.append(line)
        if brace_level == 0:
            return block_lines, i
    return block_lines, len(lines)-1  # fallback, incomplete block

for filename in sorted(os.listdir(SAVE_DIR)):
    if not filename.endswith(FILE_SUFFIX):
        continue

    print(f"Processing file: {filename}")
    with open(os.path.join(SAVE_DIR, filename), "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Extract date from first 200 lines
    date = None
    for line in lines[:200]:
        m = date_pattern.match(line.strip())
        if m:
            date = m.group(1)
            print(f"  Found date: {date}")
            break
    if not date:
        print("  No date found, skipping file")
        continue

    # Now scan for numeric blocks, filter only states by presence of state_category
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect numeric block start: e.g. 226={
        if re.match(r'^\d+\s*=\s*\{$', line):
            block_lines, block_end = extract_brace_block(lines, i)
            block_text = "".join(block_lines)

            # Check if it looks like a state by searching for 'state_category='
            if "state_category" in block_text:
                # This is a state block, parse owner and buildings from block_lines

                state_owner = None
                civs = 0
                mils = 0
                docks = 0

                # Find owner
                for bl in block_lines:
                    m = owner_pattern.search(bl)
                    if m:
                        state_owner = m.group(1)
                        break
                if not state_owner:
                    i = block_end + 1
                    continue

                # Parse buildings in the block
                # We'll look for building types inside the buildings block
                # Simple approach: find the buildings block first

                buildings_start = None
                buildings_end = None
                # Find lines where buildings block starts and ends
                for idx, bl in enumerate(block_lines):
                    if bl.strip().startswith("buildings="):
                        buildings_start = idx
                        break

                if buildings_start is not None:
                    # Extract the buildings block similarly by brace counting
                    brace_level = 0
                    for j in range(buildings_start, len(block_lines)):
                        brace_level += block_lines[j].count('{') - block_lines[j].count('}')
                        if brace_level == 0:
                            buildings_end = j
                            break

                    if buildings_end is not None:
                        buildings_block = block_lines[buildings_start+1:buildings_end]  # skip buildings= line
                        # Parse each building type block
                        current_building = None
                        inside_level = False
                        level_content = []

                        for bl in buildings_block:
                            bl_stripped = bl.strip()
                            if any(bl_stripped.startswith(bt + "=") for bt in building_types):
                                # Reset state
                                current_building = None
                                inside_level = False
                                level_content = []
                                for bt in building_types:
                                    if bl_stripped.startswith(bt + "="):
                                        current_building = bt
                                        break
                                continue
                            if current_building:
                                if bl_stripped.startswith("level="):
                                    # parse floats inside level block
                                    # extract floats between { and }
                                    floats = re.findall(r'\{([^\}]*)\}', bl_stripped)
                                    if floats:
                                        vals = floats[0].split()
                                        count = len(vals)
                                        if current_building in {"dockyard", "naval_dockyard"}:
                                            docks += count
                                        elif current_building == "arms_factory":
                                            mils += count
                                        elif current_building == "industrial_complex":
                                            civs += count

                # Save counts in timeline
                timeline_data[date][state_owner]["civs"] += civs
                timeline_data[date][state_owner]["mils"] += mils
                timeline_data[date][state_owner]["docks"] += docks

                print(f"  Parsed state {state_owner} with Civs={civs}, Mils={mils}, Docks={docks} on {date}")

            i = block_end + 1
        else:
            i += 1

print("All save data parsed.")

# Print sample output for GER
for date in sorted(timeline_data.keys()):
    if 'GER' in timeline_data[date]:
        d = timeline_data[date]['GER']
        print(f"{date}: Civs={d['civs']}, Mils={d['mils']}, Docks={d['docks']}")

# Plot GER
tag = "GER"
dates = sorted(timeline_data.keys())
civs = [timeline_data[date][tag]['civs'] if tag in timeline_data[date] else 0 for date in dates]
mils = [timeline_data[date][tag]['mils'] if tag in timeline_data[date] else 0 for date in dates]
docks = [timeline_data[date][tag]['docks'] if tag in timeline_data[date] else 0 for date in dates]

plt.plot(dates, civs, label="Civs")
plt.plot(dates, mils, label="Mils")
plt.plot(dates, docks, label="Docks")
plt.title(f"Factory counts over time for {tag}")
plt.xlabel("Date")
plt.ylabel("Factories")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
