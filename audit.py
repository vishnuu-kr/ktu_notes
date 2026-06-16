# audit_raw.py
import os

DATABASE_DIR = "database"
empty = []
tiny = []
has_module = []
no_module = []

for root, dirs, files in os.walk(DATABASE_DIR):
    if "raw.txt" not in files:
        continue
    path = os.path.join(root, "raw.txt")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    
    if len(text) < 50:
        empty.append(path)
    elif "module" in text.lower() or "Module" in text:
        has_module.append(path)
    else:
        no_module.append(path)

print(f"🔴 Empty/garbage files: {len(empty)}")
print(f"✅ Has 'Module' keyword: {len(has_module)}")
print(f"⚠️  Has text but no 'Module': {len(no_module)}")

# Show 3 samples from no_module
for p in no_module[:3]:
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        print(f"\n--- {p} ---")
        print(f.read()[:300])