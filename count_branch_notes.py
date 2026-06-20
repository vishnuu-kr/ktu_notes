import json, subprocess, collections

SUBDIR = "src/data/subjects"

def sh(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")

# semester -> list of chunk branches
sems = collections.defaultdict(list)
r = sh(["git", "branch", "-r"])
for line in r.stdout.splitlines():
    b = line.strip()
    if "auto-notes-sem-" in b and "chunk" in b:
        b = b.split("->")[0].strip()
        sem = int(b.split("sem-")[1].split("-chunk")[0])
        sems[sem].append(b)

load_tasks = []
for sem in sorted(sems):
    for br in sems[sem]:
        r_files = sh(["git", "ls-tree", "-r", "--name-only", br, SUBDIR])
        for path in r_files.stdout.splitlines():
            if path.endswith(".json") and (f"-{sem}/" in path or path.endswith(f"-{sem}.json")):
                load_tasks.append((sem, br, path))

# Run git cat-file --batch process
proc = subprocess.Popen(
    ["git", "cat-file", "--batch"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=False
)

sem_file_topics = collections.defaultdict(lambda: collections.defaultdict(dict))
processed = 0
for sem, br, path in load_tasks:
    req = f"{br}:{path}\n".encode("utf-8")
    proc.stdin.write(req)
    proc.stdin.flush()
    
    header = proc.stdout.readline().decode("utf-8", errors="replace").strip()
    if "missing" in header or not header:
        continue
    parts = header.split()
    if len(parts) < 3:
        continue
    size = int(parts[2])
    content_bytes = proc.stdout.read(size)
    proc.stdout.read(1) # consume trailing newline
    
    try:
        data = json.loads(content_bytes.decode("utf-8", errors="replace"))
    except Exception:
        continue
        
    fname = path.split("/")[-1]
    subjects = data if isinstance(data, list) else [data]
    for s in subjects:
        for m in s.get("modules", []):
            for top in m.get("topics", []):
                tid = f"{s.get('code','')}|{top.get('id','')}"
                done = bool((top.get("content") or "").strip())
                prev = sem_file_topics[sem][fname].get(tid, False)
                sem_file_topics[sem][fname][tid] = prev or done
                
    processed += 1

proc.stdin.close()
proc.wait()

print(f"{'sem':>3} {'topics':>8} {'done':>8} {'missing':>8} {'%':>5}")
grand_t = grand_done = 0
for sem in sorted(sems):
    file_topics = sem_file_topics[sem]
    t = done = 0
    for fname, topics in file_topics.items():
        t += len(topics)
        done += sum(1 for v in topics.values() if v)
    grand_t += t
    grand_done += done
    miss = t - done
    pct = (done/t*100) if t else 0
    print(f"{sem:>3} {t:>8} {done:>8} {miss:>8} {pct:>4.0f}%")

miss = grand_t - grand_done
pct = (grand_done/grand_t*100) if grand_t else 0
print("-"*40)
print(f"{'ALL':>3} {grand_t:>8} {grand_done:>8} {miss:>8} {pct:>4.0f}%")
