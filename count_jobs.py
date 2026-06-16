# minimax_swarm.py
import os
import json
import time
import requests
import itertools
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

DATABASE_DIR = "database"
KEYS_FILE = "miniall.txt"
API_BASE = "https://api.tokenrouter.com/v1/chat/completions"
MODEL = "MiniMax-M3"
MAX_WORKERS = 30

# Load keys
with open(KEYS_FILE, "r", encoding="utf-8") as f:
    MINIMAX_KEYS = [k.strip() for k in f.read().split(",") if k.strip()]

print(f"🔑 Loaded {len(MINIMAX_KEYS)} API keys")

key_pool = itertools.cycle(MINIMAX_KEYS)
key_lock = threading.Lock()

def next_key():
    with key_lock:
        return next(key_pool)

SYSTEM_PROMPT = """You are a strict syllabus data parser. Extract topics from the provided KTU syllabus module text.

RULES:
1. Use EXACT wording from the source text. Do NOT rephrase, summarize, or invent anything.
2. Extract only topic/subtopic names — not descriptions, not objectives.
3. If no clear topics exist, return an empty list.
4. Return ONLY valid JSON in this exact format, no markdown, no backticks:
{"topics": ["topic 1", "topic 2", "topic 3"]}"""


def extract_topics(module_content, api_key, retries=3):
    # Skip tiny content — nothing useful to extract
    if len(module_content.strip()) < 30:
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract topics from this syllabus text:\n\n{module_content}"}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(retries):
        try:
            resp = requests.post(API_BASE, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            content_str = data["choices"][0]["message"]["content"]

            # Guard against empty response
            if not content_str or not content_str.strip():
                return []

            parsed = json.loads(content_str)
            return parsed.get("topics", [])

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"  ⏳ Rate limit hit, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  ❌ HTTP {resp.status_code}: {e}")
            return None

        except json.JSONDecodeError:
            # Model returned non-JSON — just treat as empty
            return []

        except KeyError:
            return []

        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            if attempt < retries - 1:
                time.sleep(1)

    return None


def verify_topics(topics, source_text):
    """Reject any topic whose text doesn't appear in the source — kills hallucinations."""
    import re
    def normalize_whitespace(t):
        t = t.replace('’', "'").replace('‘', "'")
        t = t.replace('“', '"').replace('”', '"')
        t = t.replace('–', '-').replace('—', '-')
        t = re.sub(r'\s+', ' ', t)
        t = re.sub(r'-\s+', '-', t)
        return t.lower().strip()
    
    source_norm = normalize_whitespace(source_text)
    verified = []
    rejected = []
    for topic in topics:
        topic_norm = normalize_whitespace(topic)
        if topic_norm in source_norm:
            verified.append(topic)
        else:
            rejected.append(topic)
    return verified, rejected


def process_subject(subject_dir):
    subject_code = os.path.basename(subject_dir)
    out_path     = os.path.join(subject_dir, "structured.json")
    modules_path = os.path.join(subject_dir, "modules.json")
    meta_path    = os.path.join(subject_dir, "metadata.json")
    ref_path     = os.path.join(subject_dir, "reference.json")

    # Skip references and already-done subjects
    if os.path.exists(ref_path):
        return f"🔗 Skip ref:  {subject_code}"
    if os.path.exists(out_path):
        return f"⏭️  Skip done: {subject_code}"
    if not os.path.exists(modules_path):
        return f"⚠️  No modules: {subject_code}"

    try:
        with open(modules_path, "r", encoding="utf-8", errors="replace") as f:
            modules = json.load(f)
    except json.JSONDecodeError:
        return f"❌ Bad modules.json: {subject_code}"

    results = []
    had_rejection = False
    had_api_error = False

    for module in modules:
        api_key = next_key()
        content = module.get("content", "").strip()
        title   = module.get("title", module.get("module", "Unknown"))

        # Empty module content
        if not content:
            results.append({
                "module": title,
                "topics": [],
                "status": "empty_content"
            })
            continue

        # Too short to be meaningful
        if len(content) < 30:
            results.append({
                "module": title,
                "topics": [],
                "status": "too_short"
            })
            continue

        topics = extract_topics(content, api_key)

        if topics is None:
            had_api_error = True
            results.append({
                "module": title,
                "topics": [],
                "status": "api_error"
            })
            continue

        verified, rejected = verify_topics(topics, content)

        if rejected:
            had_rejection = True

        results.append({
            "module": title,
            "topics": verified,
            "rejected_topics": rejected if rejected else None,
            "status": "needs_review" if rejected else "verified"
        })

    # Save structured.json
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"❌ Save error {subject_code}: {e}"

    # Update metadata status
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8", errors="replace") as f:
                meta = json.load(f)
            if had_api_error:
                meta["extraction_status"] = "partial_error"
            elif had_rejection:
                meta["extraction_status"] = "needs_review"
            else:
                meta["extraction_status"] = "verified"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    total_topics = sum(len(r["topics"]) for r in results)

    if had_api_error:
        return f"❌ {subject_code}: api errors in some modules"
    elif had_rejection:
        return f"⚠️  {subject_code}: {len(results)} modules, {total_topics} topics (some flagged)"
    else:
        return f"✅ {subject_code}: {len(results)} modules, {total_topics} topics"


def collect_jobs():
    jobs = []
    for root, dirs, files in os.walk(DATABASE_DIR):
        if "raw.txt" not in files:
            continue
        if os.path.exists(os.path.join(root, "reference.json")):
            continue
        if os.path.exists(os.path.join(root, "structured.json")):
            continue
        if not os.path.exists(os.path.join(root, "modules.json")):
            continue
        jobs.append(root)
    return jobs


def main():
    start = time.time()
    jobs = collect_jobs()
    print(f"🚀 {len(jobs)} subjects to process with {MAX_WORKERS} workers\n")

    done = flagged = errors = skipped = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(process_subject, job): job for job in jobs}

        for future in as_completed(future_map):
            result = future.result()
            print(result)
            if result.startswith("✅"):
                done += 1
            elif result.startswith("⚠️"):
                flagged += 1
            elif result.startswith("❌"):
                errors += 1
            else:
                skipped += 1

    elapsed = time.time() - start

    print(f"\n{'='*55}")
    print(f"✅ Verified:        {done}")
    print(f"⚠️  Needs review:   {flagged}")
    print(f"❌ Errors:          {errors}")
    print(f"⏭️  Skipped:        {skipped}")
    print(f"⏱️  Total time:     {elapsed/60:.1f} minutes")
    print(f"📁 structured.json saved in each subject folder")

    if errors > 0:
        print(f"\n💡 Re-run the script to retry failed subjects — it auto-resumes.")

if __name__ == "__main__":
    main()