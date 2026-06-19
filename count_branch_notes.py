import json, subprocess, collections

SUBDIR = "src/data/subjects"

def sh(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")

def list_files(branch):
    r = sh(["git", "ls-tree", "-r", "--name-only", branch, SUBDIR])
    return [l for l in r.stdout.splitlines() if l.endswith(".json")]

def load(branch, path):
    r = sh(["git", "show", f"{branch}:{path}"])
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None

# semester -> list of chunk branches
sems = collections.defaultdict(list)
r = sh(["git", "branch", "-r"])
for line in r.stdout.splitlines():
    b = line.strip()
    if "auto-notes-sem-" in b and "chunk" in b:
        b = b.split("->")[0].strip()
        sem = int(b.split("sem-")[1].split("-chunk")[0])
        sems[sem].append(b)

grand_t = grand_done = 0
print(f"{'sem':>3} {'topics':>8} {'done':>8} {'missing':>8} {'%':>5}")
for sem in sorted(sems):
    # topic_id -> done(bool), merged across chunks, per file
    file_topics = collections.defaultdict(dict)
    # Match either folder (e.g. me-6/xxx.json) or flat file (e.g. me-6.json)
    for br in sems[sem]:
        for path in list_files(br):
            # Check if directory name is like me-6 or filename is like me-6.json
            if not (f"-{sem}/" in path or path.endswith(f"-{sem}.json")):
                continue
            data = load(br, path)
            if not data:
                continue
            fname = path.split("/")[-1]
            subjects = data if isinstance(data, list) else [data]
            for s in subjects:
                for m in s.get("modules", []):
                    for top in m.get("topics", []):
                        tid = f"{s.get('code','')}|{top.get('id','')}"
                        done = bool((top.get("content") or "").strip())
                        prev = file_topics[fname].get(tid, False)
                        file_topics[fname][tid] = prev or done
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
