import os
import re
import json

DATABASE_DIR = "database"

# Matches Module I, Module 1, Module-1, etc.
MODULE_PATTERN = re.compile(
    r'(?im)^\s*(Module\s*[-:]?\s*(?:\d+|[IVXLC]+))\b'
)

# Matches Experiment 1, 1.1, etc.
LAB_ITEM_PATTERN = re.compile(
    r'(?im)^\s*(\d{1,2}(?:\.\d{1,2})?)\s+(.+)$'
)

def detect_course_type(text, metadata=None):
    text_lower = text.lower()
    
    # 1. Try to extract directly from 'Course Type' field in the text
    m = re.search(r'course\s*type\s*[:\-\s]*([a-z\s&\+\/]+)', text_lower)
    if m:
        val = m.group(1).strip().split('\n')[0].strip()
        if any(x in val for x in ['theory']):
            return 'theory'
        if any(x in val for x in ['lab', 'practical', 'workshop', 'pcl']):
            return 'lab'

    # 2. Check metadata
    if metadata and isinstance(metadata, dict):
        ct = str(metadata.get('course_type', '')).lower()
        if any(x in ct for x in ['theory']):
            return 'theory'
        if any(x in ct for x in ['lab', 'practical', 'workshop']):
            return 'lab'

    # 3. Fallback to course code naming convention
    if metadata and 'subject_code' in metadata:
        code = str(metadata['subject_code']).upper()
        code_match = re.match(r'^([A-Z]+)\d+', code)
        if code_match:
            prefix = code_match.group(1)
            if prefix.endswith('T'):
                return 'theory'
            elif prefix.endswith('L'):
                return 'lab'

    # 4. Check if MODULE_PATTERN matches the text
    if MODULE_PATTERN.search(text):
        return 'theory'

    return 'unknown'

def parse_theory_modules_robust(text):
    text_lower = text.lower()
    
    # Locate table start
    syllabus_match = re.search(r'syllabus\s*[\r\n]*\s*module\s*[\r\n]*\s*(?:no\.?|number)?', text_lower)
    if not syllabus_match:
        syllabus_match = re.search(r'syllabus\s*[\r\n]*\s*description', text_lower)
    if not syllabus_match:
        syllabus_match = re.search(r'module\s*[\r\n]*\s*no', text_lower)
    if not syllabus_match:
        syllabus_match = re.search(r'\bsyllabus\b', text_lower)
        
    if not syllabus_match:
        return []
        
    start_char_idx = syllabus_match.end()
    
    # Locate table end
    end_pattern = re.compile(
        r'(?:course\s*assessment|text\s*book|reference\s*book|course\s*outcome|co-po\s*mapping|video\s*link|cie\s*marks|continuous\s*internal\s*evaluation)',
        re.IGNORECASE
    )
    end_match = end_pattern.search(text_lower, pos=start_char_idx)
    end_char_idx = end_match.start() if end_match else len(text)
    
    table_text = text[start_char_idx:end_char_idx]
    
    # Try splitting by explicit Module headers in table first
    module_header_pattern = re.compile(
        r'(?i)\b(Module[- ]*(?:[IVXLC]+|\d+))\b'
    )
    matches = list(module_header_pattern.finditer(table_text))
    
    if matches:
        modules = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(table_text)
            title = m.group(1).strip()
            content = table_text[m.end():end].strip()
            
            contact_hours = 'unknown'
            content_lines = [line.strip() for line in content.splitlines() if line.strip()]
            if content_lines:
                for r_idx in range(len(content_lines)-1, -1, -1):
                    val = content_lines[r_idx].lower()
                    if re.match(r'^\d+\s*(?:hrs?|hours?)?$', val):
                        contact_hours = content_lines[r_idx]
                        content_lines = content_lines[:r_idx] + content_lines[r_idx+1:]
                        break
            
            modules.append({
                'type': 'module',
                'title': title,
                'content': '\n'.join(content_lines).strip(),
                'contact_hours': contact_hours
            })
        return modules
    else:
        # Fall back to splitting by sequential row numbers
        lines = [line.strip() for line in table_text.splitlines() if line.strip()]
        modules = []
        current_module_num = 1
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if line == str(current_module_num):
                module_title = f'Module {current_module_num}'
                module_content_lines = []
                idx += 1
                next_mod_str = str(current_module_num + 1)
                while idx < len(lines):
                    sub_line = lines[idx]
                    if sub_line == next_mod_str:
                        break
                    module_content_lines.append(sub_line)
                    idx += 1
                
                contact_hours = 'unknown'
                if module_content_lines:
                    for r_idx in range(len(module_content_lines)-1, -1, -1):
                        val = module_content_lines[r_idx].strip()
                        if re.match(r'^\d+$', val):
                            contact_hours = val
                            module_content_lines = module_content_lines[:r_idx] + module_content_lines[r_idx+1:]
                            break
                            
                modules.append({
                    'type': 'module',
                    'title': module_title,
                    'content': '\n'.join(module_content_lines).strip(),
                    'contact_hours': contact_hours
                })
                current_module_num += 1
            else:
                idx += 1
        return modules

def split_lab_items(text):
    lines = text.splitlines()
    items = []
    current = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        m = LAB_ITEM_PATTERN.match(line)
        if m:
            num = m.group(1).strip()
            title = m.group(2).strip()

            if current:
                items.append(current)

            current = {
                "type": "experiment",
                "title": f"Experiment {num}",
                "content": title
            }
        else:
            if current:
                current["content"] += " " + line

    if current:
        items.append(current)

    return items

def process_subject(root):
    raw_path = os.path.join(root, "raw.txt")
    meta_path = os.path.join(root, "metadata.json")
    out_path = os.path.join(root, "modules.json")

    if not os.path.exists(raw_path):
        return ("skip", root, "no raw.txt")

    with open(raw_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read().strip()

    metadata = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except:
            metadata = {}

    course_mode = detect_course_type(text, metadata)
    parts = []

    if course_mode == "theory":
        parts = parse_theory_modules_robust(text)
        # If theory splitting failed to yield any modules, try lab splitting
        if not parts:
            parts = split_lab_items(text)
    elif course_mode == "lab":
        parts = split_lab_items(text)
        if not parts:
            parts = parse_theory_modules_robust(text)
    else:
        # Unknown mode: try theory then lab
        parts = parse_theory_modules_robust(text)
        if not parts:
            parts = split_lab_items(text)

    # Absolute fallback: if everything yields nothing, put the entire text as a single module
    if not parts:
        parts = [{
            "type": "module",
            "title": "Full Syllabus",
            "content": text,
            "contact_hours": "unknown"
        }]
        course_mode = "fallback"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parts, f, indent=2, ensure_ascii=False)

    metadata["module_split_status"] = "success"
    metadata["structure_type"] = course_mode
    metadata["module_count"] = len(parts)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return ("ok", root, f"{course_mode} -> {len(parts)} parts")

def main():
    ok = fail = skip = 0

    for root, dirs, files in os.walk(DATABASE_DIR):
        if "raw.txt" not in files:
            continue

        status, path, msg = process_subject(root)

        if status == "ok":
            ok += 1
            print(f"✅ {os.path.basename(path)}: {msg}")
        elif status == "fail":
            fail += 1
            print(f"⚠️ {os.path.basename(path)}: {msg}")
        else:
            skip += 1
            print(f"⏭️ {os.path.basename(path)}: {msg}")

    print(f"\nDone: ok={ok}, fail={fail}, skip={skip}")

if __name__ == "__main__":
    main()