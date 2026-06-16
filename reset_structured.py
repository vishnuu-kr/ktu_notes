# reset_structured.py
import os

DATABASE_DIR = "database"
count = 0

for root, dirs, files in os.walk(DATABASE_DIR):
    if "structured.json" in files:
        path = os.path.join(root, "structured.json")
        os.remove(path)
        count += 1
        print(f"🗑️  Deleted: {path}")

print(f"\n✅ Done. Removed {count} structured.json files.")