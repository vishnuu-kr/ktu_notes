import os
import json
import shutil
import re

PERFECT_DIR = "perfect"
DEST_DIR = r"C:\Users\Windows 10\Downloads\ktunode\src\data\subjects"

if os.path.exists(DEST_DIR):
    shutil.rmtree(DEST_DIR)
os.makedirs(DEST_DIR)

BRANCH_MAP = {
    # CS/IT
    'AI and Machine Learning': 'cs',
    'ArtiMachine': 'cs',
    'Artificial Intelligence': 'cs',
    'Artificial Intelligence and Data Science': 'cs',
    'Artificial Intelligence and Machine Learning': 'cs',
    'CS and Business Systems': 'cs',
    'CS and Design': 'cs',
    'CSDesign': 'cs',
    'CSE (Artificial Intelligence and Data Science)': 'cs',
    'CSE (Block Chain)': 'cs',
    'CSE (Cyber Security)': 'cs',
    'CSE (Internet of Things), CSE(IoT)': 'cs',
    'CSE (IoT and CS including Block Chain Technology)': 'cs',
    'CSandEng': 'cs',
    'Computer Science and Business Systems': 'cs',
    'Computer Science and Design': 'cs',
    'Computer Science and Engineering': 'cs',
    'Computer Science and Engineering (Artificial Intelligence and Data Science)': 'cs',
    'Computer Science and Engineering (Artificial Intelligence and Machine Learning)': 'cs',
    'Computer Science and Engineering (Artificial Intelligence)': 'cs',
    'Computer Science and Engineering (Cyber Security)': 'cs',
    'Computer Science and Engineering (Data Science)': 'cs',
    'Computer Science and Engineering (IOT)': 'cs',
    'Computer Science and Engineering and Business Systems': 'cs',
    'ComputerBusiness': 'cs',
    'ComputerCyber': 'cs',
    'ComputerEngineeringBusiness': 'cs',
    'ComputerInternet': 'cs',
    'Cse': 'cs',
    'CseAIds': 'cs',
    'CseAIms': 'cs',
    'CseData': 'cs',
    'Cseai': 'cs',
    'Cyber Security': 'cs',
    'IT': 'cs',
    'Information Technology': 'cs',
    
    # CE
    'Civil': 'ce',
    'Civil Engineering': 'ce',
    'Civil and Environmenal Engineering': 'ce',
    'Civil and Environmental Engineering': 'ce',
    
    # EC
    'Applied Electronics & Instrumentation': 'ec',
    'Applied Electronics & Instrumentation Engineering': 'ec',
    'Biomedical': 'ec',
    'Biomedical & Robotics Engineering': 'ec',
    'Biomedical Engineering': 'ec',
    'Cyber Physical System': 'ec',
    'Ece': 'ec',
    'EceComp': 'ec',
    'ElecBio': 'ec',
    'Electronics & Biomedical': 'ec',
    'Electronics & Communication Engineering': 'ec',
    'Electronics & Instrumentation': 'ec',
    'Electronics & Instrumentation Engineering': 'ec',
    'Electronics Engineering (VLSI Design and Technology)': 'ec',
    'Electronics and Biomedical Engineering': 'ec',
    'Electronics and Communication (Advanced Communication Technology)': 'ec',
    'Electronics and Communication Engineering': 'ec',
    'Electronics and Computer Engineering': 'ec',
    'ElectronicsInst': 'ec',
    'Electronics_EngineeringVLSIDesign_and_Technology_compressed': 'ec',
    'Instrumentation and Control Engineering': 'ec',
    'Robotics and Artificial Intelligence': 'ec',
    'Robotics and Automation': 'ec',
    'RoboticsAINew_compressed': 'ec',
    
    # EE
    'Elecomp': 'ee',
    'Electrical and Computer Engineering': 'ee',
    'Electrical and Electronics Engineering': 'ee',
    'ElectricalandElectronics2024Updated_compressed': 'ee',
    
    # ME
    'Aeronautical Engineering': 'me',
    'Automobile Engineering': 'me',
    'AutomobileEng': 'me',
    'Chemical': 'me',
    'Chemical Engineering': 'me',
    'Food': 'me',
    'Food Technology': 'me',
    'Indus': 'me',
    'Industrial Engineering': 'me',
    'Mechanical Engineering': 'me',
    'Mechanical Engineering (Auto)': 'me',
    'Mechanical Engineering (Automobile)': 'me',
    'MechanicalAuto': 'me',
    'Mechatronics': 'me',
    'Mechatronics Engineering': 'me',
    'Mechnaical': 'me',
    'Metallurgical & Materials Engineering': 'me',
    'Naval Architecture & Ship Building': 'me',
    'Naval Architecture & Ship Building Engineering': 'me',
    'Polymer': 'me',
    'Polymer Engineering': 'me',
    'Production': 'me',
    'Production Engineering': 'me',
    'Safety and Fire Engineering': 'me',
    'Agriculture Engineering': 'me',
    'Biotechnology': 'me',
    'Biotechnology and Biochemical Engineering': 'me',
}

GROUP_A = [
    "Computer Science and Engineering", "Artificial Intelligence", "Computer Science and Engineering (Artificial Intelligence)",
    "Computer Science and Engineering (Artificial Intelligence and Machine Learning)", "AI and Machine Learning",
    "Artificial Intelligence and Data Science", "CS and Business Systems", "CS and Design", "Cyber Security",
    "Information Technology", "Computer Science and Engineering and Business Systems", "Computer Science and Engineering (Data Science)",
    "CSE (Artificial Intelligence and Data Science)", "CSE (Internet of Things), CSE(IoT)", "CSE (Block Chain)",
    "CSE (Cyber Security)", "CSE (IoT and CS including Block Chain Technology)"
]

GROUP_B = [
    "Electronics & Communication Engineering", "Electrical and Electronics Engineering", "Electronics & Instrumentation Engineering",
    "Instrumentation and Control Engineering", "Applied Electronics & Instrumentation Engineering", "Electronics and Biomedical Engineering",
    "Cyber Physical System", "Biomedical Engineering", "Electronics and Computer Engineering", "Electrical and Computer Engineering",
    "Robotics and Artificial Intelligence", "Robotics and Automation", "Electronics Engineering (VLSI Design and Technology)",
    "Electronics and Communication (Advanced Communication Technology)"
]

GROUP_C = [
    "Civil Engineering", "Chemical Engineering", "Civil and Environmental Engineering", "Mechanical Engineering",
    "Mechanical Engineering (Auto)", "Mechanical Engineering (Automobile)", "Automobile Engineering", "Production Engineering",
    "Aeronautical Engineering", "Industrial Engineering", "Mechatronics Engineering", "Metallurgical & Materials Engineering",
    "Safety and Fire Engineering", "Polymer Engineering", "Naval Architecture & Ship Building Engineering"
]

GROUP_D = [
    "Biotechnology", "Biotechnology and Biochemical Engineering", "Agriculture Engineering", "Food Technology"
]

def map_branch_to_frontend(branch):
    if branch == "1ST YEAR SYLLABUS_KTU_GROUPA":
        return ["cs"]
    elif branch == "1ST YEAR SYLLABUS_KTU_GROUPB":
        res = []
        for b in GROUP_B:
            res.extend(map_branch_to_frontend(b))
        return list(set(res))
    elif branch == "1ST YEAR SYLLABUS_KTU_GROUPC":
        res = []
        for b in GROUP_C:
            res.extend(map_branch_to_frontend(b))
        return list(set(res))
    elif branch == "1ST YEAR SYLLABUS_KTU_GROUPD":
        res = []
        for b in GROUP_D:
            res.extend(map_branch_to_frontend(b))
        return list(set(res))
    elif branch in ["COMMON COURSES", "UCHUT347-EngineeringEthicsandSustainableDevelopment_Merged"]:
        return ["cs", "ce", "ec", "ee", "me"]
        
    mapped = BRANCH_MAP.get(branch)
    if mapped:
        return [mapped]
    return []

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
    
    # Get metadata
    meta_path = os.path.join(folder_path, 'metadata.json')
    if not os.path.exists(meta_path):
        meta_files = [f for f in os.listdir(folder_path) if f.endswith('metadata.json')]
        if meta_files: meta_path = os.path.join(folder_path, meta_files[0])
    
    if not os.path.exists(meta_path): continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
        
    # Get AI topics
    ai_files = [f for f in os.listdir(folder_path) if f.endswith('ai_perfect.json')]
    if not ai_files: continue
    
    with open(os.path.join(folder_path, ai_files[0]), 'r', encoding='utf-8') as f:
        try:
            modules_data = json.load(f)
        except:
            continue
            
    subject_code = meta.get('subject_code', 'UNKNOWN')
    
    # Get resolved subject name
    subject_name = code_to_name.get(subject_code, subject_code)
    # Fallback to parsing folder name if not resolved
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
            # Try to extract from subject code digit
            m_code = re.search(r'\d', subject_code)
            if m_code:
                sem = int(m_code.group())
                if 1 <= sem <= 8:
                    semesters = [sem]
                else:
                    semesters = [0]
            else:
                semesters = [0] # Unknown
            
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
