import os
import json

PERFECT_DIR = "perfect"
unique_branches = set()

for root, dirs, files in os.walk(PERFECT_DIR):
    for file in files:
        if file.endswith("metadata.json"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    branches = data.get("branches", [])
                    for b in branches:
                        unique_branches.add(b)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

print("Unique branches in perfect metadata:")
for b in sorted(unique_branches):
    print(f"  - {b}")
