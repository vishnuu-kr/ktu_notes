import os
import json
import itertools
import requests
import concurrent.futures
from threading import Lock

# Try to load from miniall.txt first, fallback to environment variable
API_KEYS = []
if os.path.exists("miniall.txt"):
    with open("miniall.txt", "r") as f:
        API_KEYS = [k.strip() for k in f.read().split(",") if k.strip()]

if not API_KEYS:
    API_KEYS_ENV = os.getenv("MINIMAX_API_KEYS", "")
    API_KEYS = [k.strip() for k in API_KEYS_ENV.split(",") if k.strip()]

PERFECT_DIR = "perfect"

# We now send the ENTIRE subject JSON to save 5x API calls
SYSTEM_PROMPT = """You are an expert academic syllabus editor. Your task is to format, clean, and perfect the raw syllabus topics for an entire subject.
You will receive a JSON array of objects. Each object has a "module" name and a "topics" array.
Your output must be the EXACT same JSON structure, just with the "topics" arrays perfectly cleaned.

STRICT RULES:
1. Formatting: Standardize to proper Title Case or readable Sentence Case. 
2. Noise Removal: Remove PDF artifacts like "(10 hours)", "(Ref 1)", "Chapter 2", "Module 1", trailing punctuation.
3. Zero Hallucination: NEVER invent new topics. NEVER add information that is not present in the input. Just clean what is there.
4. Smart Splitting: DO NOT split small, related concepts. Keep "Schemas and Instances" together. ONLY split a string into multiple topics if it is unusually long and clearly contains completely separate large concepts.

INPUT FORMAT:
[
  {"module": "Module 1", "topics": ["raw topic 1", "raw topic 2", "Schemas and instances"]},
  {"module": "Module 2", "topics": ["raw topic 3"]}
]

OUTPUT FORMAT:
Return ONLY the perfectly valid JSON array of objects. No markdown formatting blocks, no chat. Just the raw JSON array.
"""

# Global lock for thread-safe key cycling and progress printing
lock = Lock()
key_cycler = itertools.cycle(API_KEYS) if API_KEYS else None
processed_count = 0
total_count = 0

def refine_subject_with_minimax(struct, api_key):
    url = "https://api.tokenrouter.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "MiniMax-M3",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(struct)}
        ],
        "temperature": 0.1, 
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        if response.status_code == 429:
            return None # Rate limit hit
        response.raise_for_status()
        
        data = response.json()
        content = data['choices'][0]['message']['content'].strip()
        
        # Remove <think> blocks if present
        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()
            
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        refined_struct = json.loads(content.strip())
        return refined_struct
    except Exception as e:
        return None

def process_subject(folder_path, file_name):
    global processed_count
    
    raw_path = os.path.join(folder_path, file_name)
    out_name = "ai_perfect.json" if file_name == "structured.json" else file_name.replace("structured.json", "ai_perfect.json")
    out_path = os.path.join(folder_path, out_name)
    
    # Resume capability
    if os.path.exists(out_path):
        with lock:
            processed_count += 1
        return True

    with open(raw_path, 'r', encoding='utf-8') as f:
        struct = json.load(f)

    if not isinstance(struct, list) or len(struct) == 0:
        with lock:
            processed_count += 1
        return True

    # Get the next key safely
    with lock:
        current_api_key = next(key_cycler)
        
    refined_struct = refine_subject_with_minimax(struct, current_api_key)
    
    if refined_struct:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(refined_struct, f, indent=4, ensure_ascii=False)
        with lock:
            processed_count += 1
            if processed_count % 50 == 0:
                print(f"Progress: {processed_count}/{total_count} subjects perfectly formatted.")
        return True
    else:
        # Failure (likely rate limit), it will just skip and retry on the next GitHub Action run
        return False

def process_all():
    global total_count
    if not API_KEYS:
        print("Error: MINIMAX_API_KEYS environment variable is not set.")
        return

    subjects = [d for d in os.listdir(PERFECT_DIR) if os.path.isdir(os.path.join(PERFECT_DIR, d))]
    
    tasks = []
    for subject_folder in subjects:
        folder_path = os.path.join(PERFECT_DIR, subject_folder)
        for file in os.listdir(folder_path):
            if file.endswith("structured.json") and not file.startswith("ai_"):
                tasks.append((folder_path, file))
                
    total_count = len(tasks)
    print(f"Starting highly concurrent AI refinement on {total_count} subjects using {len(API_KEYS)} keys...")
    
    # Use 10 concurrent threads multiplied by the number of keys you provide
    max_workers = len(API_KEYS) * 5 
    # Cap to prevent overwhelming network
    max_workers = min(max_workers, 50) 
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_subject, path, file) for path, file in tasks]
        
        # Wait for all to complete
        concurrent.futures.wait(futures)

    print("Finished AI Refinement batch.")

if __name__ == "__main__":
    process_all()
