"""
KTU Premium Notes Generator V2 — High-Concurrency Async Engine
===============================================================
Designed for 30 API keys across 15 GitHub Actions runners.
Each runner handles ~10 keys with 3 concurrent requests per key = 30 threads/runner.
Total cluster: 15 runners × 30 threads = 450 concurrent API calls.

Usage:
  python generate_premium_notes_v2.py --semester 3 --chunk 0 --total-chunks 3
  
  --semester: which semester to process
  --chunk: which slice of files this runner handles (0-indexed)
  --total-chunks: how many runners share this semester
"""

import os
import requests
import json
import re
import argparse
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── Timing ──────────────────────────────────────────────────────────────────
START_TIME = time.time()
MAX_RUNTIME_SECONDS = 5.25 * 3600  # 5h 15m (safe margin for commit step)

# ─── Stats ───────────────────────────────────────────────────────────────────
stats_lock = threading.Lock()
stats = {"ok": 0, "fail": 0, "skip": 0}

# ─── System Prompt (unchanged from V1) ───────────────────────────────────────
SYSTEM_PROMPT = (
    "# SYSTEM OPERATIONAL PROTOCOL: KTU-PREMIER-ENGINE V10 (NEP 2020 / 2024 SCHEME)\n"
    "ROLE: Senior KTU (APJ Abdul Kalam Technological University, Kerala) Board Examiner & Expert Engineering Professor.\n"
    "TARGET AUDIENCE: KTU 2024 Scheme B.Tech Students (Outcome-Based Education / NEP 2020 aligned).\n"
    "OBJECTIVE: Generate premium, publication-quality, and highly-tuned B.Tech study notes specifically tailored for KTU Kerala engineering examinations. "
    "Merge rigorous academic standards of the KTU 2024 syllabus with intuitive, simple-to-understand explanations. "
    "Ensure every concept is accessible, highly structured, and visually supported by professional-grade diagrams and flawless math equations. "
    "All explanations, questions, and mark distributions must align directly with the KTU 2024 Scheme Course Outcomes (COs), Revised Bloom's Taxonomy cognitive levels, and actual Board valuation key patterns.\n\n"
    
    "## I. ACADEMIC METADATA HEADER (MANDATORY START)\n"
    "At the very beginning of your response (before any other text or anchors), you must output this exact academic context block (fully formatted in markdown):\n"
    "> **APJ ABDUL KALAM TECHNOLOGICAL UNIVERSITY (KTU) | 2024 SCHEME**\n"
    "> - **Course:** {COURSE_INFO}\n"
    "> - **Module:** {MODULE_INFO}\n"
    "> - **Topic:** {TOPIC}\n\n"

    "## II. STRICT COMPARTMENTALIZATION (MANDATORY HOOKS)\n"
    "You must wrap your response inside these EXACT 5 HTML anchor pairs. "
    "Use the exact string labels below. Do not add any text, preamble, or extra tags outside these blocks.\n\n"
    "Required anchor pair format:\n"
    "<!-- SECTION_1_START -->\n... section 1 content ...\n<!-- SECTION_1_END -->\n\n"
    "<!-- SECTION_2_START -->\n... section 2 content ...\n<!-- SECTION_2_END -->\n\n"
    "<!-- SECTION_3_START -->\n... section 3 content ...\n<!-- SECTION_3_END -->\n\n"
    "<!-- SECTION_4_START -->\n... section 4 content ...\n<!-- SECTION_4_END -->\n\n"
    "<!-- SECTION_5_START -->\n... section 5 content ...\n<!-- SECTION_5_END -->\n\n"

    "### 1. Core Technical Definition & Intuitive Overview (inside SECTION_1)\n"
    "- Provide the formal, rigorous academic definition using exact KTU 2024 syllabus terminology.\n"
    "- **Conceptual Analogy / Intuition**: Explain the concept in simple, plain English using a real-world analogy. Make it immediately clear to a student reading it for the first time.\n"
    "- Explicitly state any physical constants or standard metrics in **bold**.\n"
    "- Use markdown callout boxes (e.g., `> [!NOTE]` or `> [!IMPORTANT]`) to highlight core definitions and syllabus highlights.\n\n"

    "### 2. Deep Theoretical Analysis & KTU High-Yield Formula Sheet (inside SECTION_2)\n"
    "- Break down the operational concept or theorem into structured, bulleted logic steps.\n"
    "- Highlight the core 'Why' and 'How' behind each step to keep the explanation accessible.\n"
    "- **KTU Formula Sheet / Cheat Sheet**: Provide a concise markdown table summarizing all key formulas, equations, boundary conditions, and units required for solving problems on this topic. "
    "CRITICAL: Never use the vertical pipe symbol `|` inside table rows (like for absolute value `|x|`). Use `\\vert` or `\\mid` to avoid breaking the markdown table syntax.\n"
    "- Explain the real-world utility of this system or equation in engineering fields.\n\n"

    "### 3. Step-by-Step Derivations & Analytical Matrix (inside SECTION_3)\n"
    "- **Exhaustive Content Mandate**: You are strictly prohibited from using defensive shortcuts, truncation phrases, or step-skipping placeholders. Every algebraic transition or numerical evaluation step must be explicitly written out.\n"
    "- Show the exhaustive derivation. Multi-line equations must be wrapped inside a single standard alignment block using `\\begin{aligned} ... \\end{aligned}`. Every step must contain a text row explaining the conversion logic. Use $$ for display equations and $ for inline. Ensure there is one blank line before and after every $$ block.\n\n"

    "### 4. Structural Diagrams & Schematics (inside SECTION_4)\n"
    "- **Mermaid Compilation Safeguards**:\n"
    "  * Node Identifier Alpha Rule: Every node ID must be purely alphanumeric and prefixed with letters (e.g., `node1`, `stepA`). Never use reserved keywords (`end`, `subgraph`, `graph`, `style`) as standalone node names.\n"
    "  * Label Formatting Restriction: Inside double-quoted node labels, never insert markdown formatting tags like bold (`**`), italics (`*`), or HTML tables. Use raw, clean uppercase alphanumeric text for clarity.\n"
    "- Diagram Fallback: If a topic requires complex physical drawings, adapt the Mermaid block to render a highly detailed **Block-Level Functional Architecture Flow** mapping the interactions instead of attempting physical drawings.\n\n"

    "### 5. KTU 2024 Scheme Examination Question Bank & Topic Recap (inside SECTION_5)\n"
    "- Generate highly relevant practice test problems modeled precisely after the KTU 2024 Scheme assessment regulations. Tag each question with a simulated KTU Past Year Question tag (e.g., `[KTU University Exam - Dec 2023]`).\n"
    "  - **Part A Questions (3 Marks)**: Two direct short-answer conceptual/definition questions with precise model answers.\n"
    "  - **Part B Questions (14 Marks)**: Provide a true KTU ESE Module Internal Choice. Generate TWO completely independent alternative selections: **Question A (14 Marks)** and **Question B (14 Marks)**.\n"
    "    * Each question choice must feature sub-parts (e.g., part (a) for 7 marks and part (b) for 7 marks).\n"
    "    * For every sub-question, provide the complete, step-by-step model solution.\n"
    "  - **KTU Examiner's Valuation Warning / Pitfall Callout**: Add a warning callout (`> [!WARNING]`) explaining exactly where students commonly lose marks on this type of question.\n"
    "- **Topic Recap & Important Things to Remember**: At the very end of SECTION_5, provide a high-density, bulleted summary serving as a rapid-revision checklist.\n\n"

    "## III. EXECUTION CONSTRAINTS (STRICT)\n"
    "1. NO PYTHON/CODING FOR NON-CS TOPICS: Strictly prohibit the use of Python code, algorithms, or programming snippets in Mathematics, Physics, Chemistry, Management, or core non-CS engineering subjects (Civil, Mechanical, etc.). Introducing programming into unrelated subjects is strictly forbidden.\n"
    "2. ADAPTIVE COMPLEXITY: Adapt the depth of the explanation to the topic's complexity. For simple introductory topics, provide a concise, high-level overview. For complex analytical topics, drastically increase the depth, mathematical rigor, and step-by-step detail.\n"
    "3. ZERO CHITCHAT: Start directly with the Academic Metadata Header.\n"
    "4. LATEX ISOLATION: Exactly one blank line immediately before and after every standalone $$ block.\n"
    "5. NO INTRO/OUTRO MARKS: HTML comment anchors must reside alone on lines without code block backticks wrapping them.\n"
    "6. ANTI-HALLUCINATION PROTOCOL: NEVER fabricate textbook references, edition numbers, or author names. All formulas must be mathematically verifiable."
)


def is_time_up():
    """Check if we're approaching the runtime limit."""
    return (time.time() - START_TIME) > MAX_RUNTIME_SECONDS


def fetch_notes(topic_title, course_info, module_info, api_key):
    """Call the LLM API with retry logic and exponential backoff."""
    prompt = (SYSTEM_PROMPT
              .replace("{COURSE_INFO}", course_info)
              .replace("{MODULE_INFO}", module_info)
              .replace("{TOPIC}", topic_title))
    
    user_content = f"Generate notes for topic: '{topic_title}' from {module_info}.\nExecute KTU-PREMIER-ENGINE V10."

    api_url = os.environ.get("API_URL", "https://api.tokenrouter.com/v1/chat/completions")
    model_name = os.environ.get("MODEL_NAME", "MiniMax-M3")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1
    }

    max_retries = 4
    for attempt in range(max_retries):
        if is_time_up():
            return None
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=300)
            
            # Handle rate limiting specifically
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", (attempt + 1) * 15))
                print(f"  [RATE-LIMITED] Key ...{api_key[-6:]}, waiting {retry_after}s", flush=True)
                time.sleep(retry_after)
                continue
                
            resp.raise_for_status()
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if not content:
                raise ValueError("API returned empty content")
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            return content
            
        except requests.exceptions.HTTPError as e:
            if resp.status_code in (500, 502, 503):
                wait_time = (attempt + 1) * 10
                print(f"  [SERVER-ERR] {resp.status_code} for '{topic_title[:40]}...', retry in {wait_time}s (Attempt {attempt+1}/{max_retries})", flush=True)
                time.sleep(wait_time)
            else:
                print(f"  [HTTP-ERR] {resp.status_code}: {str(e)[:100]}", flush=True)
                if attempt == max_retries - 1:
                    raise
                time.sleep((attempt + 1) * 5)
        except requests.exceptions.Timeout:
            wait_time = (attempt + 1) * 10
            print(f"  [TIMEOUT] '{topic_title[:40]}...', retry in {wait_time}s (Attempt {attempt+1}/{max_retries})", flush=True)
            time.sleep(wait_time)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (attempt + 1) * 10
            print(f"  [RETRY] '{topic_title[:40]}...' error: {str(e)[:80]}. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})", flush=True)
            time.sleep(wait_time)
    
    return None


class KeyPool:
    """Round-robin key distributor with per-key concurrency limiting."""
    
    def __init__(self, keys, max_per_key=1):
        self.keys = keys
        self.max_per_key = max_per_key
        self.semaphores = {k: threading.Semaphore(max_per_key) for k in keys}
        self._idx = 0
        self._lock = threading.Lock()
    
    def acquire(self):
        """Get a key and acquire its semaphore. Returns (key, release_fn)."""
        attempts = 0
        while attempts < len(self.keys) * 2:
            with self._lock:
                key = self.keys[self._idx % len(self.keys)]
                self._idx += 1
            
            if self.semaphores[key].acquire(blocking=True, timeout=5):
                return key, lambda k=key: self.semaphores[k].release()
            attempts += 1
        
        # Fallback: block on first available key
        key = self.keys[0]
        self.semaphores[key].acquire()
        return key, lambda: self.semaphores[key].release()


def topic_needs_generation(topic):
    """Check if a topic still needs content generated."""
    content = topic.get('content', '')
    if not content:
        return True
    if "Coming Soon" in content:
        return True
    if len(content) < 500:
        return True
    return False


def process_file(file_path, key_pool, max_workers):
    """Process a single subject JSON file with high concurrency."""
    print(f"\nProcessing file: {file_path}", flush=True)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Collect all pending tasks
    tasks = []
    for subject in data:
        course_name = f"{subject.get('code', '')} - {subject.get('name', '')}"
        for module in subject.get('modules', []):
            module_name = module.get('title', 'Unknown Module')
            for topic in module.get('topics', []):
                if topic_needs_generation(topic):
                    tasks.append((topic, course_name, module_name))
    
    total_in_file = sum(
        len(topic) 
        for subject in data 
        for module in subject.get('modules', [])
        for topic in [module.get('topics', [])]
    )
    pending = len(tasks)
    already_done = total_in_file - pending
    
    print(f"  Total topics: {total_in_file} | Already done: {already_done} | Pending: {pending}", flush=True)
    
    if pending == 0:
        print(f"  [SKIP] All topics already generated.", flush=True)
        return
    
    updated = False
    save_counter = 0
    SAVE_EVERY = 25  # Save progress every 25 successful generations
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        submitted = 0
        
        for (topic, course_name, module_name) in tasks:
            if is_time_up():
                print("  [TIME] Approaching limit, stopping new submissions...", flush=True)
                break
            
            # Acquire a key from the pool
            key, release_fn = key_pool.acquire()
            
            # Stagger submissions: 1 second between each thread start
            # to avoid cold-start burst on the API
            if submitted > 0 and submitted < max_workers:
                time.sleep(1)
            
            future = executor.submit(
                _generate_with_release,
                topic['title'], course_name, module_name, key, release_fn
            )
            futures[future] = topic
            submitted += 1
        
        # Collect results
        for future in as_completed(futures):
            topic = futures[future]
            try:
                content = future.result()
                if content:
                    topic['content'] = content
                    updated = True
                    save_counter += 1
                    with stats_lock:
                        stats["ok"] += 1
                    print(f"  [OK] Generated: {topic['title']}", flush=True)
                    
                    # Periodic save to avoid losing progress
                    if save_counter >= SAVE_EVERY:
                        _save_file(file_path, data)
                        save_counter = 0
                else:
                    with stats_lock:
                        stats["fail"] += 1
            except Exception as e:
                with stats_lock:
                    stats["fail"] += 1
                print(f"  [FAIL] {topic['title']}: {str(e)[:100]}", flush=True)
    
    # Final save
    if updated:
        _save_file(file_path, data)


def _generate_with_release(topic_title, course_name, module_name, key, release_fn):
    """Wrapper that ensures the key semaphore is released after the API call."""
    try:
        return fetch_notes(topic_title, course_name, module_name, key)
    finally:
        release_fn()


def _save_file(file_path, data):
    """Atomic file save."""
    temp_path = file_path + ".tmp"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, file_path)
    print(f"  [SAVED] {file_path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="KTU Premium Notes Generator V2")
    parser.add_argument("--semester", required=True, type=int, help="Semester number (1-8)")
    parser.add_argument("--chunk", required=True, type=int, help="Chunk index for this runner (0-indexed)")
    parser.add_argument("--total-chunks", required=True, type=int, help="Total chunks this semester is split into")
    parser.add_argument("--branch", default="ALL", help="Branches to process (comma-separated or ALL)")
    parser.add_argument("--max-per-key", type=int, default=3, help="Max concurrent requests per API key")
    args = parser.parse_args()
    
    # Load all API keys
    with open("miniall.txt", "r", encoding="utf-8") as f:
        all_keys = [k.strip() for k in f.read().split(",") if k.strip()]
    
    total_keys = len(all_keys)
    print(f"Loaded {total_keys} API keys", flush=True)
    
    # KEY DISTRIBUTION STRATEGY:
    # ─────────────────────────────────────────────────────────────────────
    # Each runner gets ALL keys, but limits concurrency per key.
    # Since multiple runners hit the same keys simultaneously, the effective
    # per-key load = max_per_key × number_of_active_runners.
    #
    # With 30 keys, 10 runners, max_per_key=1:
    #   Per runner: 30 concurrent (1 per key × 30 keys)
    #   Per key total: 10 requests (from 10 runners)
    #   Cluster total: 300 concurrent
    #
    # With 30 keys, 10 runners, max_per_key=2:
    #   Per runner: 60 concurrent
    #   Per key total: 20 requests
    #   Cluster total: 600 concurrent (aggressive, may rate limit)
    #
    # RECOMMENDATION: Start with max_per_key=1, bump to 2 if no rate limits.
    # ─────────────────────────────────────────────────────────────────────
    my_keys = all_keys  # Every runner gets all keys
    
    if not my_keys:
        print(f"ERROR: No API keys found in miniall.txt", flush=True)
        sys.exit(1)
    
    print(f"Runner config: Semester {args.semester}, Chunk {args.chunk}/{args.total_chunks}", flush=True)
    print(f"Assigned {len(my_keys)} API keys", flush=True)
    
    # Initialize key pool with per-key concurrency limit
    key_pool = KeyPool(my_keys, max_per_key=args.max_per_key)
    max_workers = min(len(my_keys) * args.max_per_key, 10)  # Cap at 10 concurrent per runner
    print(f"Max concurrent requests: {max_workers} (capped to avoid API overload)", flush=True)
    
    # Find data directory
    data_dir = "src/data/subjects"
    if not os.path.exists(data_dir):
        data_dir = "../ktunode/src/data/subjects"
    if not os.path.exists(data_dir):
        print(f"ERROR: Cannot find data directory", flush=True)
        sys.exit(1)
    
    # Gather target files for this semester
    sem_id = args.semester
    allowed_branches = args.branch.split(",") if args.branch != "ALL" else None
    
    target_files = []
    for f in sorted(os.listdir(data_dir)):
        if f.endswith(f"-{sem_id}.json"):
            branch = f.replace(f"-{sem_id}.json", "")
            if allowed_branches is None or branch in allowed_branches:
                target_files.append(os.path.join(data_dir, f))
    
    # Split files across chunks
    # Each chunk gets a subset of files for this semester
    chunk_files = []
    for i, f in enumerate(target_files):
        if i % args.total_chunks == args.chunk:
            chunk_files.append(f)
    
    print(f"\nFiles for this chunk: {len(chunk_files)} of {len(target_files)} total", flush=True)
    for f in chunk_files:
        print(f"  → {os.path.basename(f)}", flush=True)
    print("", flush=True)
    
    # Process each file
    for filepath in chunk_files:
        if is_time_up():
            print("\n[TIME] MAX RUNTIME REACHED. Exiting gracefully.", flush=True)
            break
        process_file(filepath, key_pool, max_workers)
    
    # Print summary
    elapsed = time.time() - START_TIME
    print(f"\n{'='*60}", flush=True)
    print(f"GENERATION COMPLETE", flush=True)
    print(f"  Generated: {stats['ok']}", flush=True)
    print(f"  Failed:    {stats['fail']}", flush=True)
    print(f"  Runtime:   {elapsed/60:.1f} minutes", flush=True)
    print(f"  Rate:      {stats['ok']/(elapsed/60):.1f} topics/min" if elapsed > 60 else "", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
