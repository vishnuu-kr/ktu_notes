# test_swarm_sample.py
import os
import json
import re
import time
import requests
import itertools
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

DATABASE_DIR = "database"
KEYS_FILE    = "miniall.txt"
API_BASE = "https://api.tokenrouter.com/v1/chat/completions"
MODEL    = "MiniMax-M3"
MAX_WORKERS  = 60

import hashlib

GLOBAL_CACHE = {}
cache_lock = threading.Lock()

with open(KEYS_FILE, "r", encoding="utf-8") as f:
    MINIMAX_KEYS = [k.strip() for k in f.read().split(",") if k.strip()]

print(f"🔑 Loaded {len(MINIMAX_KEYS)} API keys")

key_pool = itertools.cycle(MINIMAX_KEYS)
key_lock  = threading.Lock()

def next_key():
    with key_lock:
        return next(key_pool)

SYSTEM_PROMPT = """You are a strict KTU syllabus data parser.

Your job: Extract the list of TOPICS or EXPERIMENTS from the syllabus text below.

STRICT RULES:
1. Use EXACT wording from the source. Do NOT rephrase, summarize, or invent.
2. For theory subjects: extract topic/subtopic names from each Module section.
3. Skip course objectives, prerequisites, exam details — extract ONLY content topics.
4. If nothing found, return empty list.
5. Return ONLY this JSON format, no markdown, no backticks:
{"topics": ["topic 1", "topic 2"]}"""

def get_content_key(text):
    t = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"').replace('–', '-').replace('—', '-')
    t = re.sub(r'\s+', ' ', t).lower().strip()
    return hashlib.sha256(t.encode('utf-8')).hexdigest()

def prepopulate_cache():
    count = 0
    for root, dirs, files in os.walk(DATABASE_DIR):
        if "structured.json" in files and "modules.json" in files:
            try:
                with open(os.path.join(root, "modules.json"), "r", encoding="utf-8") as f:
                    mods = json.load(f)
                with open(os.path.join(root, "structured.json"), "r", encoding="utf-8") as f:
                    structs = json.load(f)
                
                for m, s in zip(mods, structs):
                    content = m.get("content", "").strip()
                    if content:
                        key = get_content_key(content)
                        if s.get("status") == "verified":
                            GLOBAL_CACHE[key] = s.get("topics", [])
                            count += 1
            except Exception:
                pass
    print(f"💾 Prepopulated cache with {len(GLOBAL_CACHE)} unique module extractions (from {count} completed chunks)")

def extract_topics(content, api_key, retries=3):
    if len(content.strip()) < 20:
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Extract topics from this KTU syllabus:\n\n{content}"}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(retries):
        try:
            resp = requests.post(API_BASE, headers=headers, json=payload, timeout=45)
            resp.raise_for_status()
            data        = resp.json()
            content_str = data["choices"][0]["message"]["content"]

            if not content_str or not content_str.strip():
                return []

            # Strip <think>...</think> reasoning block if present
            content_clean = re.sub(r'(?s)<think>.*?</think>', '', content_str).strip()
            # Strip markdown fences if present
            if content_clean.startswith("```"):
                content_clean = re.sub(r'^```[a-zA-Z]*\s*', '', content_clean)
                content_clean = re.sub(r'\s*```$', '', content_clean)
            content_clean = content_clean.strip()

            parsed = json.loads(content_clean)
            return parsed.get("topics", [])

        except requests.exceptions.HTTPError:
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"  ⏳ Rate limit, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  ❌ HTTP {resp.status_code}")
            return None

        except json.JSONDecodeError:
            return []
        except KeyError:
            return []
        except Exception as e:
            print(f"  ❌ Error: {e}")
            if attempt < retries - 1:
                time.sleep(1)

    return None

def verify_topics(topics, source_text):
    def normalize_whitespace(t):
        t = t.replace('’', "'").replace('‘', "'")
        t = t.replace('“', '"').replace('”', '"')
        t = t.replace('–', '-').replace('—', '-')
        t = re.sub(r'\s+', ' ', t)
        t = re.sub(r'-\s+', '-', t)
        return t.lower().strip()
    
    source_norm = normalize_whitespace(source_text)
    verified, rejected = [], []
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

    if os.path.exists(os.path.join(subject_dir, "reference.json")):
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

    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8", errors="replace") as f:
                meta = json.load(f)
        except Exception:
            pass

    # Use the pre-split modules from modules.json directly
    chunks = modules
    detected_type = meta.get("structure_type", "unknown")

    results        = []
    had_rejection  = False
    had_api_error  = False

    for chunk in chunks:
        content = chunk["content"].strip()
        title   = chunk["title"]

        if len(content) < 20:
            results.append({"module": title, "topics": [], "status": "too_short"})
            continue

        # Check Cache
        content_key = get_content_key(content)
        with cache_lock:
            cached_topics = GLOBAL_CACHE.get(content_key)

        if cached_topics is not None:
            results.append({
                "module": title,
                "topics": cached_topics,
                "rejected_topics": None,
                "status": "verified"
            })
            continue

        api_key = next_key()
        topics = extract_topics(content, api_key)

        if topics is None:
            had_api_error = True
            results.append({"module": title, "topics": [], "status": "api_error"})
            continue

        verified, rejected = verify_topics(topics, content)
        if rejected:
            had_rejection = True
        else:
            if topics is not None:
                with cache_lock:
                    GLOBAL_CACHE[content_key] = verified

        results.append({
            "module": title,
            "topics": verified,
            "rejected_topics": rejected if rejected else None,
            "status": "needs_review" if rejected else "verified"
        })

    # Save
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"❌ Save error {subject_code}: {e}"

    # Update metadata
    try:
        meta["extraction_status"] = (
            "partial_error" if had_api_error else
            "needs_review"  if had_rejection else
            "verified"
        )
        meta["detected_type"] = detected_type
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    total_topics = sum(len(r["topics"]) for r in results)

    if had_api_error:
        return f"❌ {subject_code}: API errors"
    elif had_rejection:
        return f"⚠️  {subject_code}: {len(results)} modules, {total_topics} topics (flagged)"
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
    prepopulate_cache()
    # Process only the first 5 subjects to test the swarm safely
    jobs  = collect_jobs()[:5]
    print(f"🚀 [TEST RUN] {len(jobs)} subjects to process with {MAX_WORKERS} workers\n")

    done = flagged = errors = skipped = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(process_subject, job): job for job in jobs}
        for future in as_completed(future_map):
            result = future.result()
            print(result)
            if   result.startswith("✅"): done    += 1
            elif result.startswith("⚠️"): flagged += 1
            elif result.startswith("❌"): errors  += 1
            else:                         skipped += 1

    elapsed = time.time() - start
    print(f"\n{'='*55}")
    print(f"✅ Verified:       {done}")
    print(f"⚠️  Needs review:  {flagged}")
    print(f"❌ Errors:         {errors}")
    print(f"⏭️  Skipped:       {skipped}")
    print(f"⏱️  Total time:    {elapsed/60:.1f} minutes")
    print(f"\n💡 Test run complete! Run minimax_swarm.py for the full run.")

if __name__ == "__main__":
    main()
