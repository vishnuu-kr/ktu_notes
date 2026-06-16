import os
import json
import re

PERFECT_DIR = "perfect"

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

# Test mapping
unmapped = set()
mapped_counts = {}

for d in os.listdir(PERFECT_DIR):
    folder_path = os.path.join(PERFECT_DIR, d)
    if not os.path.isdir(folder_path): continue
    
    meta_path = os.path.join(folder_path, "metadata.json")
    if not os.path.exists(meta_path):
        meta_files = [f for f in os.listdir(folder_path) if f.endswith('metadata.json')]
        if meta_files: meta_path = os.path.join(folder_path, meta_files[0])
        
    if not os.path.exists(meta_path): continue
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    branches = meta.get("branches", [])
    for b in branches:
        mapped = map_branch_to_frontend(b)
        if not mapped:
            unmapped.add(b)
        else:
            for m in mapped:
                mapped_counts[m] = mapped_counts.get(m, 0) + 1

print("Unmapped branches:", unmapped)
print("Mapped subject-branch counts:", mapped_counts)
