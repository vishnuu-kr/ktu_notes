import json

extra_mappings = {
    "Aeronautical Engineering": ["aeronautical-engineering"],
    "Agriculture Engineering": ["agriculture-engineering"],
    "Applied Electronics & Instrumentation": ["applied-electronics-and-instrumentation"],
    "Applied Electronics & Instrumentation Engineering": ["applied-electronics-and-instrumentation"],
    "Artificial Intelligence": ["artificial-intelligence"],
    "Artificial Intelligence and Data Science": ["artificial-intelligence-and-data-science"],
    "Artificial Intelligence and Machine Learning": ["artificial-intelligence-and-machine-learning"],
    "Automobile Engineering": ["automobile-engineering"],
    "Biomedical Engineering": ["biomedical-engineering"],
    "Biotechnology": ["biotechnology-engineering"],
    "Biotechnology and Biochemical Engineering": ["biotechnology-and-biochemical-engineering"],
    "CS and Business Systems": ["computer-science-and-business-systems"],
    "CS and Design": ["computer-science-and-design"],
    "CSE (Artificial Intelligence and Data Science)": ["artificial-intelligence-and-data-science"],
    "CSE (Block Chain)": ["computer-science-and-engineering-internet-of-things-and-cyber-security-including-blockchain-technology"],
    "CSE (Cyber Security)": ["computer-science-and-engineering-cyber-security"],
    "CSE (Internet of Things), CSE(IoT)": ["computer-science-and-engineering-iot"],
    "CSE (IoT and CS including Block Chain Technology)": ["computer-science-and-engineering-internet-of-things-and-cyber-security-including-blockchain-technology"],
    "Chemical Engineering": ["chemical-engineering"],
    "Civil Engineering": ["civil-engineering"],
    "Civil and Environmenal Engineering": ["civil-and-environmental-engineering"],
    "Civil and Environmental Engineering": ["civil-and-environmental-engineering"],
    "Computer Science and Business Systems": ["computer-science-and-business-systems"],
    "Computer Science and Design": ["computer-science-and-design"],
    "Computer Science and Engineering": ["computer-science-and-engineering"],
    "Computer Science and Engineering (Artificial Intelligence and Data Science)": ["artificial-intelligence-and-data-science"],
    "Computer Science and Engineering (Artificial Intelligence and Machine Learning)": ["artificial-intelligence-and-machine-learning"],
    "Computer Science and Engineering (Artificial Intelligence)": ["computer-science-and-engineering-artificial-intelligence"],
    "Computer Science and Engineering (Cyber Security)": ["computer-science-and-engineering-cyber-security"],
    "Computer Science and Engineering (Data Science)": ["computer-science-and-engineering-data-science"],
    "Computer Science and Engineering (IOT)": ["computer-science-and-engineering-iot"],
    "Computer Science and Engineering and Business Systems": ["computer-science-and-engineering-and-business-systems"],
    "Cyber Physical System": ["cyber-physical-systems"],
    "Cyber Security": ["computer-science-and-engineering-cyber-security"],
    "Electrical and Computer Engineering": ["electrical-and-computer-engineering"],
    "Electrical and Electronics Engineering": ["electrical-and-electronics-engineering"],
    "Electronics & Biomedical": ["electronics-and-biomedical-engineering"],
    "Electronics & Communication Engineering": ["electronics-and-communication-engineering"],
    "Electronics & Instrumentation": ["electronics-and-instrumentation"],
    "Electronics & Instrumentation Engineering": ["electronics-and-instrumentation"],
    "Electronics Engineering (VLSI Design and Technology)": ["electronics-engineering-vlsi-design-and-technology"],
    "Electronics and Biomedical Engineering": ["electronics-and-biomedical-engineering"],
    "Electronics and Communication (Advanced Communication Technology)": ["electronics-and-communication-advanced-communication-technology"],
    "Electronics and Communication Engineering": ["electronics-and-communication-engineering"],
    "Electronics and Computer Engineering": ["electronics-and-computer-engineering"],
    "Food Technology": ["food-technology"],
    "Industrial Engineering": ["industrial-engineering"],
    "Information Technology": ["information-technology"],
    "Instrumentation and Control Engineering": ["instrumentation-and-control"],
    "Mechanical Engineering": ["mechanical-engineering"],
    "Mechanical Engineering (Auto)": ["mechanical-automobile-engineering"],
    "Mechanical Engineering (Automobile)": ["mechanical-automobile-engineering"],
    "Mechatronics Engineering": ["mechatronics-engineering"],
    "Naval Architecture & Ship Building": ["naval-architecture-and-shipbuilding-engineering"],
    "Naval Architecture & Ship Building Engineering": ["naval-architecture-and-shipbuilding-engineering"],
    "Polymer Engineering": ["polymer-engineering"],
    "Production Engineering": ["production-engineering"],
    "Robotics and Artificial Intelligence": ["robotics-and-artificial-intelligence"],
    "Robotics and Automation": ["robotics-and-automation"],
    "Safety and Fire Engineering": ["safety-and-fire-engineering"]
}

with open("resolved_branch_map.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

added = 0
for k, v in extra_mappings.items():
    if k not in mapping:
        mapping[k] = v
        added += 1
    else:
        # Merge arrays and deduplicate
        merged = list(set(mapping[k] + v))
        if len(merged) > len(mapping[k]):
            mapping[k] = merged
            added += 1

with open("resolved_branch_map.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)

print(f"Done. Added or updated {added} mapping keys in resolved_branch_map.json.")
