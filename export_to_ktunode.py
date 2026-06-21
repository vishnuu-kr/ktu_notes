import os
import json
import shutil
import re

PERFECT_DIR = "perfect"
DEST_DIR = r"C:\Users\Windows 10\Downloads\ktunode\src\data\subjects"

if os.path.exists(DEST_DIR):
    shutil.rmtree(DEST_DIR)
os.makedirs(DEST_DIR)

with open("resolved_branch_map.json", "r", encoding="utf-8") as f:
    RESOLVED_BRANCH_MAP = json.load(f)

def map_branch_to_frontend(branch):
    return RESOLVED_BRANCH_MAP.get(branch, [])

def slugify(text):
    return re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()

def is_all_caps(line):
    line = line.strip()
    if not line:
        return False
    if not any(c.isupper() for c in line):
        return False
    if any(c.islower() for c in line):
        return False
    clean = re.sub(r'[^A-Za-z]', '', line)
    if len(clean) < 3:
        return False
    line_lower = line.lower()
    if "semester" in line_lower or "group" in line_lower or "common" in line_lower:
        return False
    if "b.tech" in line_lower or "apj abdul" in line_lower or "university" in line_lower:
        return False
    return True

def extract_subject_name(text, match_start):
    before_text = text[max(0, match_start-300):match_start]
    
    # Try finding explicit COURSE NAME label first
    m = re.search(r'(?:COURSE\s+NAME|Name\s+of\s+Course|Course\s+Name)[\s:]+([^\n]+)', before_text, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        name = re.sub(r'[^a-zA-Z0-9\s\-,&()]', '', name).strip()
        name = re.sub(r'\(Group.*?\)', '', name, flags=re.IGNORECASE).strip()
        if len(name) > 5:
            return name

    lines = [line.strip() for line in before_text.splitlines() if line.strip()]
    if not lines:
        return ""
        
    caps_lines = []
    caps_indices = []
    for i, line in enumerate(lines):
        if is_all_caps(line):
            caps_lines.append(line)
            caps_indices.append(i)
            
    if not caps_lines:
        return ""
        
    last_caps_idx = caps_indices[-1]
    contiguous_caps = [caps_lines[-1]]
    expected_idx = last_caps_idx - 1
    
    for idx in range(len(caps_indices) - 2, -1, -1):
        if caps_indices[idx] == expected_idx:
            contiguous_caps.append(caps_lines[idx])
            expected_idx -= 1
        else:
            break
            
    contiguous_caps.reverse()
    return " ".join(contiguous_caps)

print("Building subject code to subject name map...")
code_to_name = {}
OUTPUT_DIR = "output"
for root, dirs, files in os.walk(OUTPUT_DIR):
    for file in files:
        if file == "raw.txt":
            pdf_path = os.path.join(root, file)
            with open(pdf_path, "r", encoding="utf-8") as f:
                text = f.read()
            pattern = re.compile(r"Course\s*Code\s*([A-Z]{2,10}\d{3})", re.IGNORECASE)
            for match in pattern.finditer(text):
                code = match.group(1).upper()
                name = extract_subject_name(text, match.start())
                if name:
                    if code not in code_to_name or len(name) > len(code_to_name[code]):
                        code_to_name[code] = name

print(f"Map complete! Found names for {len(code_to_name)} unique course codes.")

# Group subjects by (branchId, semester)
branch_sem_subjects = {}

for folder in os.listdir(PERFECT_DIR):
    folder_path = os.path.join(PERFECT_DIR, folder)
    if not os.path.isdir(folder_path): continue
    
    # Get all metadata files in the directory
    meta_files = []
    if os.path.exists(os.path.join(folder_path, 'metadata.json')):
        meta_files.append('metadata.json')
    for f in os.listdir(folder_path):
        if f.endswith('metadata.json') and f != 'metadata.json':
            meta_files.append(f)
            
    for meta_file in meta_files:
        meta_path = os.path.join(folder_path, meta_file)
        with open(meta_path, 'r', encoding='utf-8') as f:
            try:
                meta = json.load(f)
            except Exception as e:
                print(f"Error reading metadata {meta_path}: {e}")
                continue
                
        # Find corresponding ai_perfect file
        if meta_file == 'metadata.json':
            ai_file = 'ai_perfect.json'
        else:
            prefix = meta_file.replace('_metadata.json', '')
            ai_file = f'{prefix}_ai_perfect.json'
            
        ai_path = os.path.join(folder_path, ai_file)
        if not os.path.exists(ai_path):
            any_ai = [f for f in os.listdir(folder_path) if f.endswith('ai_perfect.json')]
            if any_ai:
                ai_path = os.path.join(folder_path, any_ai[0])
            else:
                continue
                
        with open(ai_path, 'r', encoding='utf-8') as f:
            try:
                modules_data = json.load(f)
            except:
                continue
                
        subject_code = meta.get('subject_code', 'UNKNOWN')
        
        # Get resolved subject name
        subject_name = code_to_name.get(subject_code, subject_code)
        if subject_name == subject_code:
            subject_name = folder
            if " - " in folder:
                subject_name = folder.split(" - ", 1)[1].strip()
                
        semester_str = meta.get('semester', '')
        
        semesters = []
        if "S1/S2" in semester_str or "1/2" in semester_str:
            semesters = [1, 2]
        else:
            m = re.search(r'\d+', semester_str)
            if m:
                semesters = [int(m.group())]
            else:
                m_code = re.search(r'\d', subject_code)
                if m_code:
                    sem = int(m_code.group())
                    if 1 <= sem <= 8:
                        semesters = [sem]
                    else:
                        semesters = [0]
                else:
                    semesters = [0]
                
        branches = meta.get('branches', [])
        
        # Map modules to frontend format
        frontend_modules = []
        for mod in modules_data:
            mod_num = mod.get('module', 0)
            mod_title = mod.get('title', f'Module {mod_num}')
            topics = mod.get('topics', [])
            
            frontend_topics = []
            for i, t in enumerate(topics):
                frontend_topics.append({
                    "id": f"t{mod_num}_{i+1}",
                    "title": t,
                    "content": "",
                    "pyqs": []
                })
                
            frontend_modules.append({
                "id": f"m{mod_num}",
                "title": mod_title,
                "topics": frontend_topics
            })
            
        # Add to mapped branches and semesters
        for branch in branches:
            mapped_ids = map_branch_to_frontend(branch)
            for mapped_id in mapped_ids:
                for sem in semesters:
                    key = (mapped_id, sem)
                    if key not in branch_sem_subjects:
                        branch_sem_subjects[key] = []
                        
                    sub_id = slugify(f"{subject_code}-{mapped_id}-s{sem}")
                    
                    subject_obj = {
                        "id": sub_id,
                        "code": subject_code,
                        "name": subject_name,
                        "branchId": mapped_id,
                        "semester": sem,
                        "modules": frontend_modules
                    }
                    branch_sem_subjects[key].append(subject_obj)

# Deduplicate and write to disk
total_written = 0
for (branch_id, sem), subjects in branch_sem_subjects.items():
    if sem == 0:
        continue
        
    # Deduplicate by subject code within the same branch and semester
    seen_codes = set()
    deduped_subjects = []
    for s in subjects:
        if s['code'] not in seen_codes:
            seen_codes.add(s['code'])
            deduped_subjects.append(s)
            
    filename = f"{branch_id}-{sem}.json"
    filepath = os.path.join(DEST_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(deduped_subjects, f, indent=2, ensure_ascii=False)
    total_written += len(deduped_subjects)
    print(f"Exported {len(deduped_subjects)} subjects to {filename}")

print(f"Export complete! Total of {total_written} subjects written to {DEST_DIR}")
