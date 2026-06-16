import os
import json

PERFECT_DIR = "perfect"

# Canonical Mapping for specific folders
MAPPING = {
    "Cse": ["Computer Science and Engineering"],
    "IT": ["Information Technology"],
    "Mechnaical": ["Mechanical Engineering"],
    "Civil": ["Civil Engineering"],
    "Ece": ["Electronics and Communication Engineering"],
    "Elecomp": ["Electrical and Computer Engineering"],
    "ElectricalandElectronics2024Updated_compressed": ["Electrical and Electronics Engineering"],
    "Chemical": ["Chemical Engineering"],
    
    "Artificial Intelligence": ["Artificial Intelligence"],
    "Cseai": ["Computer Science and Engineering (Artificial Intelligence)"],
    "CseAIds": ["Computer Science and Engineering (Artificial Intelligence and Data Science)"],
    "CseAIms": ["Computer Science and Engineering (Artificial Intelligence and Machine Learning)"],
    "CseData": ["Computer Science and Engineering (Data Science)"],
    "Cyber": ["Computer Science and Engineering (Cyber Security)"],
    "ComputerBusiness": ["Computer Science and Business Systems"],
    "ComputerEngineeringBusiness": ["Computer Science and Engineering and Business Systems"],
    "ComputerInternet": ["Computer Science and Engineering (IOT)"],
    "CSDesign": ["Computer Science and Design"],
    "CSandEng": ["Computer Science and Engineering"],
    "ArtiData": ["Artificial Intelligence and Data Science"],
    "ArtiMachine": ["Artificial Intelligence and Machine Learning"],
    
    "Mechatronics": ["Mechatronics Engineering"],
    "AutomobileEng": ["Automobile Engineering"],
    "MechanicalAuto": ["Mechanical Engineering (Automobile)"],
    "CivilEnv": ["Civil and Environmenal Engineering"],
    "Electronics_EngineeringVLSIDesign_and_Technology_compressed": ["Electronics Engineering (VLSI Design and Technology)"],
    "ElectronicsInst": ["Electronics & Instrumentation"],
    "EceComp": ["Electronics and Computer Engineering"],
    "ElecBio": ["Electronics & Biomedical"],
    
    "RoboticsAINew_compressed": ["Robotics and Artificial Intelligence"],
    "RoboticsAutomation": ["Robotics and Automation"],
    "BioRob": ["Biomedical & Robotics Engineering"],
    "Biomedical": ["Biomedical Engineering"],
    "BiotechBio": ["Biotechnology and Biochemical Engineering"],
    "Biotechnology": ["Biotechnology"],
    "Agri": ["Agriculture Engineering"],
    "Food": ["Food Technology"],
    "Polymer": ["Polymer Engineering"],
    "Naval": ["Naval Architecture & Ship Building"],
    "Production": ["Production Engineering"],
    "Indus": ["Industrial Engineering"],
    "Safety": ["Safety and Fire Engineering"],
    "InstrumentationControl": ["Instrumentation and Control Engineering"],
    "AppEleIns": ["Applied Electronics & Instrumentation"],
    
    "ORGANIZATIONAL BEHAVIOUR AND BUSINESS COMMUNICATION": ["COMMON COURSES"],
    "PROJECT MANAGEMENT _ PLANNING, EXECUTION,EVALUATIONAND CONTROL": ["COMMON COURSES"]
}

# Group mappings (Cleaned of punctuation)
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

MAPPING["1ST YEAR SYLLABUS_KTU_GROUPA"] = GROUP_A
MAPPING["1ST YEAR SYLLABUS_KTU_GROUPB"] = GROUP_B
MAPPING["1ST YEAR SYLLABUS_KTU_GROUPC"] = GROUP_C
MAPPING["1ST YEAR SYLLABUS_KTU_GROUPD"] = GROUP_D


def clean_branches():
    processed_files = 0
    total_folders = 0
    
    for folder in os.listdir(PERFECT_DIR):
        folder_path = os.path.join(PERFECT_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
            
        total_folders += 1
        meta_path = os.path.join(folder_path, 'metadata.json')
        
        # In case the file is named branch_metadata.json
        if not os.path.exists(meta_path):
            meta_files = [f for f in os.listdir(folder_path) if f.endswith('metadata.json')]
            if meta_files:
                meta_path = os.path.join(folder_path, meta_files[0])
                
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                try:
                    meta = json.load(f)
                except:
                    continue
            
            original_branches = meta.get('branches', [])
            new_branches = set()
            
            for b in original_branches:
                if b in MAPPING:
                    new_branches.update(MAPPING[b])
                else:
                    new_branches.add(b)
                    
            # Update file if there are changes
            if set(original_branches) != new_branches:
                meta['branches'] = sorted(list(new_branches))
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, indent=4, ensure_ascii=False)
                processed_files += 1

    print(f"Branch cleanup complete! Updated {processed_files} metadata files across {total_folders} subjects.")

if __name__ == '__main__':
    clean_branches()
