# debug_agri.py
import os, json

# Check one theory and one lab subject
paths = [
    r"database\branch\Agri\PCAGT302\modules.json",
    r"database\branch\Agri\PCAGL308\modules.json",
    r"database\branch\Agri\OEAGT832\modules.json",
]

for path in paths:
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        continue

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        modules = json.load(f)

    print(f"\n=== {path} ===")
    print(f"Type: {type(modules)}, Count: {len(modules)}")
    for i, m in enumerate(modules):
        content = m.get("content", "")
        print(f"  [{i}] type={m.get('type')} title={m.get('title','?')[:40]}")
        print(f"       content_len={len(content)} preview={repr(content[:80])}")