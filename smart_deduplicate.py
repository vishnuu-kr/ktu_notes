# smart_deduplicate.py
import os
import json
import re
from collections import defaultdict

DATABASE_DIR = "database"

def normalize(text):
    """Strip whitespace, punctuation noise for comparison."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def similarity_ratio(a, b):
    """Simple character overlap ratio."""
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    shorter = min(len(a), len(b))
    longer = max(len(a), len(b))
    # Compare first 500 chars as fingerprint
    a_sample = a[:500]
    b_sample = b[:500]
    matches = sum(c1 == c2 for c1, c2 in zip(a_sample, b_sample))
    return matches / max(len(a_sample), len(b_sample))

def read_raw(folder):
    path = os.path.join(folder, "raw.txt")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()

def main():
    by_code = defaultdict(list)
    for root, dirs, files in os.walk(DATABASE_DIR):
        if "raw.txt" in files:
            by_code[os.path.basename(root)].append(root)

    duplicates = {k: v for k, v in by_code.items() if len(v) > 1}

    SIMILARITY_THRESHOLD = 0.85  # 85% similar = treat as same subject

    truly_unique = []     # Same code, actually different content
    near_identical = []   # Same code, ~same content (PDF formatting noise)
    canonical_map = {}

    for code, folders in duplicates.items():
        texts = [(f, read_raw(f)) for f in folders]

        # Compare all against first
        base_text = texts[0][1]
        all_similar = all(
            similarity_ratio(base_text, t) >= SIMILARITY_THRESHOLD
            for _, t in texts[1:]
        )

        if all_similar:
            # Near-identical — deduplicate safely
            canonical = folders[0]
            canonical_map[code] = canonical
            near_identical.append(code)

            for dup in folders[1:]:
                ref = {
                    "is_reference": True,
                    "canonical_path": canonical,
                    "subject_code": code,
                    "reason": "near_identical_content"
                }
                with open(os.path.join(dup, "reference.json"), "w") as f:
                    json.dump(ref, f, indent=2)
        else:
            # Truly different — keep all, tag with branch info
            truly_unique.append(code)
            for folder in folders:
                branch = folder.split(os.sep)[2] if len(folder.split(os.sep)) > 2 else "unknown"
                meta_path = os.path.join(folder, "metadata.json")
                meta = {}
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        try:
                            meta = json.load(f)
                        except:
                            pass
                meta["shared_elective"] = True
                meta["branch_variant"] = branch
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)

    print(f"✅ Near-identical (safe to deduplicate): {len(near_identical)}")
    print(f"⚠️  Truly different variants (electives): {len(truly_unique)}")
    print(f"🔗 Canonical map entries: {len(canonical_map)}")

    with open("canonical_map.json", "w") as f:
        json.dump(canonical_map, f, indent=2)

    # Save elective variants list for reference
    with open("elective_variants.json", "w") as f:
        json.dump(truly_unique, f, indent=2)

    print("\n📄 Saved canonical_map.json and elective_variants.json")

if __name__ == "__main__":
    main()