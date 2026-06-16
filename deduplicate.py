# deduplicate.py
import os
import json
import shutil
from collections import defaultdict

DATABASE_DIR = "database"

def get_content_hash(folder):
    """Hash based on raw.txt content to detect true duplicates."""
    raw_path = os.path.join(folder, "raw.txt")
    if not os.path.exists(raw_path):
        return None
    with open(raw_path, "r", encoding="utf-8", errors="replace") as f:
        return hash(f.read().strip())

def main():
    # Group all subject folders by subject_code
    by_code = defaultdict(list)

    for root, dirs, files in os.walk(DATABASE_DIR):
        if "raw.txt" not in files:
            continue
        subject_code = os.path.basename(root)
        by_code[subject_code].append(root)

    duplicates = {k: v for k, v in by_code.items() if len(v) > 1}
    print(f"Found {len(duplicates)} subject codes with duplicates\n")

    canonical_map = {}  # code -> canonical path

    for code, folders in duplicates.items():
        # Check if content is actually identical
        hashes = [(get_content_hash(f), f) for f in folders]
        unique_hashes = set(h for h, _ in hashes if h)

        if len(unique_hashes) == 1:
            # Truly identical — pick first as canonical
            canonical = folders[0]
            canonical_map[code] = canonical

            for duplicate in folders[1:]:
                ref = {
                    "is_reference": True,
                    "canonical_path": canonical,
                    "subject_code": code
                }
                ref_path = os.path.join(duplicate, "reference.json")
                with open(ref_path, "w") as f:
                    json.dump(ref, f, indent=2)
                print(f"🔗 {code}: {os.path.dirname(duplicate).split(os.sep)[-1]} → canonical")

        else:
            # Content differs — keep all, mark as variants
            print(f"⚠️  {code}: {len(folders)} variants with DIFFERENT content")
            for i, (h, folder) in enumerate(hashes):
                meta_path = os.path.join(folder, "metadata.json")
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        meta = json.load(f)
                    meta["variant_note"] = f"variant_{i+1}_of_{len(folders)}"
                    with open(meta_path, "w") as f:
                        json.dump(meta, f, indent=2)

    print(f"\n✅ Done. {len(canonical_map)} codes deduplicated.")

    # Save the canonical map
    with open("canonical_map.json", "w") as f:
        json.dump(canonical_map, f, indent=2)
    print("📄 Saved canonical_map.json")

if __name__ == "__main__":
    main()