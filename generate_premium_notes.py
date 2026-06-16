import os
import requests
import json
import re
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Using the requested refined system prompt
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

import time
import sys

# Track start time for graceful shutdown
START_TIME = time.time()
MAX_RUNTIME_SECONDS = 5.5 * 3600  # 5.5 hours

lock = threading.Lock()

def fetch_notes_from_minimax(topic, course, module, api_key):
    prompt = SYSTEM_PROMPT.replace("{COURSE_INFO}", course).replace("{MODULE_INFO}", module).replace("{TOPIC}", topic)
    user_content = f"Generate notes for topic: '{topic}' from {module}.\nExecute KTU-PREMIER-ENGINE V10."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "MiniMax-M3",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post("https://api.tokenrouter.com/v1/chat/completions", headers=headers, json=payload, timeout=300)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            return content
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = (attempt + 1) * 10
            print(f"[RETRY] '{topic}' failed due to: {str(e)}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})", flush=True)
            time.sleep(wait_time)

def process_file(file_path, keys):
    print(f"Processing file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    updated = False
    
    with ThreadPoolExecutor(max_workers=len(keys)) as executor:
        futures_dict = {}
        key_idx = 0
        
        for subject in data:
            course_name = f"{subject.get('courseCode', '')} - {subject.get('courseName', '')}"
            for module in subject.get('modules', []):
                module_name = module.get('title', 'Unknown Module')
                for topic in module.get('topics', []):
                    # Graceful shutdown check
                    if time.time() - START_TIME > MAX_RUNTIME_SECONDS:
                        print("MAX RUNTIME REACHED (5.5 Hours). Gracefully halting task scheduling to allow saving...", flush=True)
                        break
                        
                    # Skip if already has content that isn't a placeholder
                    if topic.get('content') and "Coming Soon" not in topic['content'] and len(topic['content']) > 500:
                        continue
                        
                    future = executor.submit(
                        fetch_notes_from_minimax, 
                        topic['title'], course_name, module_name, keys[key_idx % len(keys)]
                    )
                    futures_dict[future] = topic
                    key_idx += 1
                
                if time.time() - START_TIME > MAX_RUNTIME_SECONDS:
                    break
            if time.time() - START_TIME > MAX_RUNTIME_SECONDS:
                break
                    
        from concurrent.futures import as_completed
        for future in as_completed(futures_dict):
            topic = futures_dict[future]
            try:
                content = future.result()
                if content:
                    topic['content'] = content
                    updated = True
                    print(f"[OK] Generated: {topic['title']}", flush=True)
            except Exception as e:
                print(f"[FAIL] {topic['title']}: {str(e)}", flush=True)
                
    if updated:
        # Atomic saving
        temp_path = file_path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, file_path)
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", default="ALL")
    parser.add_argument("--semester", required=True)
    args = parser.parse_args()
    
    with open("miniall.txt", "r", encoding="utf-8") as f:
        all_keys = [k.strip() for k in f.read().split(",") if k.strip()]
        
    sem_id = int(args.semester)
    # Slice keys: 5 matrix jobs, 6 keys each
    start_idx = (sem_id - 1) * 6
    end_idx = min(sem_id * 6, len(all_keys))
    keys = all_keys[start_idx:end_idx]
    
    if not keys:
        print(f"Warning: No keys allocated for semester {sem_id}. Falling back to key 0.")
        keys = [all_keys[0]] if all_keys else []
        
    print(f"Assigned {len(keys)} API keys for Semester {sem_id}")
        
    data_dir = r"../ktunode/src/data/subjects"
    # Fallback to local if running via CI where they might be same dir
    if not os.path.exists(data_dir):
        data_dir = r"src/data/subjects"
        
    allowed_branches = args.branch.split(",")
    
    target_files = []
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(f"-{sem_id}.json"):
                branch = f.replace(f"-{sem_id}.json", "")
                if args.branch == "ALL" or branch in allowed_branches:
                    target_files.append(os.path.join(data_dir, f))
                    
    print(f"Found {len(target_files)} target files to process for Semester {sem_id}.")
    for f in target_files:
        if time.time() - START_TIME > MAX_RUNTIME_SECONDS:
            print("MAX RUNTIME REACHED (5.5 Hours). Exiting gracefully.")
            break
        process_file(f, keys)
