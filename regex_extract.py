# regex_extract.py — Regex-first topic extraction with MiniMax fallback
import os
import re
import json
import time
import hashlib
import requests
import itertools
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

DATABASE_DIR = "database"
KEYS_FILE = "miniall.txt"
API_BASE = "https://api.tokenrouter.com/v1/chat/completions"
MODEL = "MiniMax-M3"
MAX_WORKERS = 60

# ── Lazy Load API keys ──
MINIMAX_KEYS = []
key_pool = None
key_lock = threading.Lock()

def load_keys():
    global MINIMAX_KEYS, key_pool
    if MINIMAX_KEYS:
        return
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                MINIMAX_KEYS = [k.strip() for k in f.read().split(",") if k.strip()]
            key_pool = itertools.cycle(MINIMAX_KEYS)
        except Exception:
            pass

def next_key():
    with key_lock:
        load_keys()
        if not MINIMAX_KEYS:
            raise RuntimeError("API key file miniall.txt is missing, but MiniMax fallback was triggered!")
        return next(key_pool)

# ── Stats ──
stats = Counter()
stats_lock = threading.Lock()

# ═══════════════════════════════════════════
#  REGEX TOPIC EXTRACTION (no AI needed)
# ═══════════════════════════════════════════

def clean_content(content):
    """Remove reference markers, textbook refs, contact hours from module content."""
    # Remove [Text 1: ...] and (Text-2) etc
    content = re.sub(r'\[Text\s*[-:]?\s*\d*:?[^\]]*\]', '', content)
    content = re.sub(r'\(Text\s*[-:]?\s*\d*:?[^\)]*\)', '', content)
    # Remove trailing textbook/reference lines
    content = re.sub(r'Text\s*(?:Books?|book)\s*:.*$', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'Reference\s*(?:Books?|book)\s*:.*$', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Normalize contact hours: (3 hours), (1 hour), (3 hours), 1 hour, 3 hrs etc
    content = re.sub(r'\(\s*\d+\s*(?:hour|hr)s?\s*\)', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\b\d+\s*(?:hour|hr)s?\b', '', content, flags=re.IGNORECASE)
    
    # Handle hyphenation at line breaks
    content = re.sub(r'-\n', '-', content)
    # Normalize whitespace
    content = re.sub(r'\n', ' ', content)
    
    # Normalize weird characters (especially PDF dashes/bullets)
    content = content.replace('\ufffd', ' - ')
    content = content.replace('–', ' - ')
    content = content.replace('—', ' - ')
    content = content.replace('−', ' - ')
    
    content = re.sub(r'\s+', ' ', content)
    return content.strip()


def protect_abbreviations(text):
    """Protect abbreviations from being split on periods."""
    # Protect initials like N.D.M.C., D.D.A.
    text = re.sub(r'(?<=[A-Z])\.(?=[A-Z]\.?)', '@@DOT@@', text)
    # Protect common abbreviations
    text = re.sub(
        r'\b(St|Dr|Mr|Mrs|Ms|vs|etc|i\.e|e\.g|Jr|Sr|No|Nos|Vol|Fig|Eq|Eqn|approx|Prof)\.\s*',
        r'\1@@DOT@@ ', text
    )
    return text


def restore_dots(text):
    return text.replace('@@DOT@@', '.')


# Common hyphenated words that should not be split
HYPHENATED_WORDS = {
    "no", "load", "star", "delta", "cross", "validation", "3", "phase", "single", "two", 
    "built", "in", "steady", "state", "band", "gap", "analog", "to", "digital", "high", 
    "speed", "low", "pass", "voltage", "controlled", "phase", "locked", "pn", 
    "junction", "dc", "ac", "three", "four", "half", "full", "on", "off", "self", "excited",
    "open", "circuit", "short", "nptel", "youtube", "close", "loop", "sub",
    "systems", "co", "axial", "de", "excitation", "multi", "level", "in", "plane", "out",
    "of", "pocket", "real", "time", "wide", "area", "large", "scale", "small", "mid",
    "long", "term", "short", "day", "night", "off", "peak", "on", "grid", "off", "grid",
    "state", "of", "the", "art", "end", "to", "end", "key", "value", "read", "write",
    "run", "time", "decision", "making", "quasi", "static", "electro", "magnetic",
    "radio", "frequency", "ultra", "wide", "infra", "red", "light", "emitting", "laser",
    "carrier", "to", "noise", "bit", "error", "rate", "power", "factor"
}


def split_by_dashes_smart(text):
    # Split text by '-' and rejoin segments that are parts of hyphenated words or short particles
    raw_segments = text.split('-')
    if len(raw_segments) <= 1:
        return [text]
        
    segments = []
    current = raw_segments[0].strip()
    
    for i in range(1, len(raw_segments)):
        next_seg = raw_segments[i].strip()
        
        # Check if we should merge current and next_seg because they form a hyphenated word
        last_word = current.split()[-1].lower() if current.split() else ""
        first_word = next_seg.split()[0].lower() if next_seg.split() else ""
        
        # Strip punctuation from words for check
        last_word_clean = re.sub(r'\W+', '', last_word)
        first_word_clean = re.sub(r'\W+', '', first_word)
        
        should_merge = False
        if (last_word_clean in HYPHENATED_WORDS or 
            first_word_clean in HYPHENATED_WORDS or
            len(last_word_clean) <= 2 or 
            len(first_word_clean) <= 2 or
            last_word_clean.isdigit() or
            first_word_clean.isdigit()):
            should_merge = True
            
        if should_merge:
            current = f"{current}-{raw_segments[i]}"
        else:
            if current.strip():
                segments.append(current.strip())
            current = raw_segments[i]
            
    if current.strip():
        segments.append(current.strip())
        
    return segments


def extract_topics_regex(content):
    """Extract topic names directly from module content text using delimiter detection."""
    content = clean_content(content)
    if not content or len(content) < 10:
        return None  # Too short, can't parse

    content = protect_abbreviations(content)

    # Check if there is an introductory part (e.g. "Applied Probability: Basics...")
    # If a colon exists and is followed by space and not a digit, split off the prefix
    colon_match = re.search(r'^([^:]+):\s+([A-Z].*)$', content)
    if colon_match:
        content = colon_match.group(2).strip()

    topics = []

    # Count structural delimiters
    semicolons = content.count(';')
    commas = content.count(',')
    sentence_breaks = len(re.findall(r'\.\s+[A-Z]', content))
    space_dashes = content.count(' - ')

    # Strategy: detect dominant delimiter
    if semicolons >= 1:
        # Split by semicolons
        raw = content.split(';')
        for r in raw:
            r = restore_dots(r.strip().rstrip('.').strip())
            if r:
                topics.append(r)
    elif commas >= 3 and commas >= sentence_breaks:
        # Split by commas
        raw = content.split(',')
        for r in raw:
            r = restore_dots(r.strip().rstrip('.').strip())
            if r:
                topics.append(r)
    elif space_dashes >= 2:
        # Split by space-dash-space
        raw = content.split(' - ')
        for r in raw:
            r = restore_dots(r.strip().rstrip('.').strip())
            if r:
                topics.append(r)
    elif '-' in content:
        # Smart dash splitting
        raw = split_by_dashes_smart(content)
        for r in raw:
            r = restore_dots(r.strip().rstrip('.').strip())
            if r:
                topics.append(r)
    elif sentence_breaks >= 1:
        # Split by sentence boundaries
        raw = re.split(r'(?<=\.)\s+(?=[A-Z])', content)
        for r in raw:
            r = restore_dots(r.strip().rstrip('.').strip())
            if r:
                topics.append(r)
    else:
        # Fallback: single topic
        cleaned = restore_dots(content.strip().rstrip('.').strip())
        if cleaned:
            topics.append(cleaned)

    # Clean up topics: remove leading/trailing non-words and ensure length > 3
    final_topics = []
    for t in topics:
        t = re.sub(r'^\W+|\W+$', '', t).strip()
        if len(t) > 3:
            final_topics.append(t)

    return final_topics if final_topics else None


# ═══════════════════════════════════════════
#  MINIMAX FALLBACK (only for edge cases)
# ═══════════════════════════════════════════

SYSTEM_PROMPT = """You are a strict KTU syllabus data parser.

STRICT RULES:
1. Use EXACT wording from the source. Do NOT rephrase, summarize, or invent.
2. Copy topic names character-for-character from the text.
3. Return ONLY this JSON format, no markdown, no backticks:
{"topics": ["topic 1", "topic 2"]}"""


def extract_topics_minimax(content, api_key, retries=3):
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
            {"role": "user", "content": f"Extract topics from this KTU syllabus:\n\n{content}"}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }
    for attempt in range(retries):
        try:
            resp = requests.post(API_BASE, headers=headers, json=payload, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            content_str = data["choices"][0]["message"]["content"]
            if not content_str or not content_str.strip():
                return []
            content_clean = re.sub(r'(?s)<think>.*?</think>', '', content_str).strip()
            if content_clean.startswith("```"):
                content_clean = re.sub(r'^```[a-zA-Z]*\s*', '', content_clean)
                content_clean = re.sub(r'\s*```$', '', content_clean)
            parsed = json.loads(content_clean.strip())
            return parsed.get("topics", [])
        except requests.exceptions.HTTPError:
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            return None
        except (json.JSONDecodeError, KeyError):
            return []
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
    return None


def verify_topics(topics, source_text):
    """Check each topic appears in source text."""
    def norm(t):
        t = t.replace('\u2018', "'").replace('\u2019', "'")
        t = t.replace('\u201c', '"').replace('\u201d', '"')
        t = t.replace('\u2013', '-').replace('\u2014', '-')
        t = re.sub(r'\s+', ' ', t)
        t = re.sub(r'-\s+', '-', t)
        return t.lower().strip()

    source_norm = norm(source_text)
    verified, rejected = [], []
    for topic in topics:
        if norm(topic) in source_norm:
            verified.append(topic)
        else:
            rejected.append(topic)
    return verified, rejected


# ═══════════════════════════════════════════
#  MAIN PROCESSING
# ═══════════════════════════════════════════

def process_subject(subject_dir):
    code = os.path.basename(subject_dir)
    out_path = os.path.join(subject_dir, "structured.json")
    modules_path = os.path.join(subject_dir, "modules.json")
    meta_path = os.path.join(subject_dir, "metadata.json")

    if os.path.exists(os.path.join(subject_dir, "reference.json")):
        return f"🔗 Skip ref:  {code}"
    if os.path.exists(out_path):
        return f"⏭️  Skip done: {code}"
    if not os.path.exists(modules_path):
        return f"⚠️  No modules: {code}"

    try:
        with open(modules_path, "r", encoding="utf-8", errors="replace") as f:
            modules = json.load(f)
    except json.JSONDecodeError:
        return f"❌ Bad modules.json: {code}"

    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8", errors="replace") as f:
                meta = json.load(f)
        except Exception:
            pass

    results = []
    method_used = "regex"

    for chunk in modules:
        content = chunk.get("content", "").strip()
        title = chunk.get("title", "Module")

        if len(content) < 20:
            results.append({"module": title, "topics": [], "status": "too_short"})
            continue

        # Try regex first
        topics = extract_topics_regex(content)

        if topics is not None and len(topics) >= 1:
            # Regex succeeded
            with stats_lock:
                stats["regex_ok"] += 1
            results.append({
                "module": title,
                "topics": topics,
                "rejected_topics": None,
                "status": "verified"
            })
        else:
            # Fallback to MiniMax
            method_used = "minimax"
            api_key = next_key()
            topics = extract_topics_minimax(content, api_key)

            if topics is None:
                with stats_lock:
                    stats["api_error"] += 1
                results.append({"module": title, "topics": [], "status": "api_error"})
                continue

            verified, rejected = verify_topics(topics, content)
            with stats_lock:
                stats["minimax_ok"] += 1
                if rejected:
                    stats["minimax_rejected"] += 1

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
        return f"❌ Save error {code}: {e}"

    # Update metadata
    try:
        has_error = any(r["status"] == "api_error" for r in results)
        has_review = any(r["status"] == "needs_review" for r in results)
        meta["extraction_status"] = (
            "partial_error" if has_error else
            "needs_review" if has_review else
            "verified"
        )
        meta["extraction_method"] = method_used
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    total = sum(len(r["topics"]) for r in results)
    icon = "✅" if method_used == "regex" else "🤖"
    return f"{icon} {code}: {len(results)} modules, {total} topics ({method_used})"


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
    print(f"🚀 {len(jobs)} subjects to process (regex-first, MiniMax fallback)\n")

    done = flagged = errors = skipped = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(process_subject, job): job for job in jobs}
        for future in as_completed(future_map):
            result = future.result()
            print(result)
            if result.startswith("✅") or result.startswith("🤖"):
                done += 1
            elif result.startswith("⚠️"):
                flagged += 1
            elif result.startswith("❌"):
                errors += 1
            else:
                skipped += 1

    elapsed = time.time() - start
    print(f"\n{'='*55}")
    print(f"✅ Processed:      {done}")
    print(f"⚠️  Flagged:       {flagged}")
    print(f"❌ Errors:         {errors}")
    print(f"⏭️  Skipped:       {skipped}")
    print(f"⏱️  Time:          {elapsed:.1f}s")
    print(f"\n📊 Method breakdown:")
    print(f"   Regex OK:       {stats['regex_ok']}")
    print(f"   MiniMax OK:     {stats['minimax_ok']}")
    print(f"   MiniMax reject: {stats['minimax_rejected']}")
    print(f"   API errors:     {stats['api_error']}")


if __name__ == "__main__":
    main()
