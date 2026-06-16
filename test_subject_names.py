import os
import re

INPUT_DIR = "output"

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
    lines = [line.strip() for line in before_text.splitlines() if line.strip()]
    if not lines:
        return "UNKNOWN"
        
    caps_lines = []
    caps_indices = []
    for i, line in enumerate(lines):
        if is_all_caps(line):
            caps_lines.append(line)
            caps_indices.append(i)
            
    if not caps_lines:
        return "UNKNOWN"
        
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

results = []
for root, dirs, files in os.walk(INPUT_DIR):
    for file in files:
        if file == "raw.txt":
            pdf_path = os.path.join(root, file)
            with open(pdf_path, "r", encoding="utf-8") as f:
                text = f.read()
            pattern = re.compile(r"Course\s*Code\s*([A-Z]{2,10}\d{3})", re.IGNORECASE)
            for match in pattern.finditer(text):
                code = match.group(1).upper()
                name = extract_subject_name(text, match.start())
                results.append(f"{code} -> {name}")

with open("names_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print(f"Extraction tested! Saved {len(results)} matches to names_log.txt.")
