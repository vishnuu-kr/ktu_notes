import subprocess, collections

def sh(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")

# gather branches
r = sh(["git", "branch", "-r"])
branches = []
for line in r.stdout.splitlines():
    b = line.strip().split("->")[0].strip()
    if "auto-notes-sem-" in b and "chunk" in b:
        branches.append(b)

print(f"{'branch':40} {'file':14} {'MB':>8}")
flagged = []
for br in branches:
    # git ls-tree with sizes
    r = sh(["git", "ls-tree", "-r", "-l", br, "src/data/subjects"])
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        size = parts[3]
        path = " ".join(parts[4:])
        if not path.endswith(".json") or size == "-":
            continue
        mb = int(size) / (1024*1024)
        if mb > 50:  # only show the heavy ones
            fname = path.split("/")[-1]
            print(f"{br:40} {fname:14} {mb:>8.1f}")
            if mb > 100:
                flagged.append((br, fname, mb))

print("\n=== OVER 100 MB (push will be rejected) ===")
for br, fname, mb in flagged:
    print(f"{br}  {fname}  {mb:.1f} MB")
if not flagged:
    print("none over 100MB in pushed branches (oversized commits were rejected, so they're not here)")
