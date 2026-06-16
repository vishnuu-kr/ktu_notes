import os
import re
import json
import shutil

INPUT_DIR = "output"
OUTPUT_DIR = "database"

def determine_category(folder_name):
    """Categorize the folder based on its name."""
    name_lower = folder_name.lower()
    if "1st year" in name_lower or "group" in name_lower:
        return "first_year", folder_name.strip()
    elif "common" in name_lower:
        return "common", "Common Courses"
    else:
        return "branch", folder_name.strip()

def build_database():
    print(f"🚀 Initializing KTU Syllabus Pipeline...")
    
    # Clean slate: Remove existing database to avoid duplicates during testing
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    total_subjects_found = 0
    all_subjects_registry = []

    # Walk through the output directory
    for root, dirs, files in os.walk(INPUT_DIR):
        if "raw.txt" not in files:
            continue

        folder_name = os.path.basename(root)
        category, sub_category = determine_category(folder_name)
        
        path = os.path.join(root, "raw.txt")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # Find all occurrences of Course Code to use as anchor points
        # Captures the exact code (e.g., GAMAT101, PCCST302)
        pattern = re.compile(r"Course\s*Code\s*([A-Z]{2,10}\d{3})", re.IGNORECASE)
        matches = list(pattern.finditer(text))

        if not matches:
            print(f"⚠️ No subjects found in {folder_name}")
            continue

        print(f"📂 Processing {folder_name} ({len(matches)} subjects found)")

        # Split the text based on Course Code anchors
        for i, match in enumerate(matches):
            subject_code = match.group(1).upper()
            
            # The start of this subject's text block is the start of this match
            start_idx = match.start()
            
            # The end is the start of the next match, or the end of the file
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
            
            subject_raw_text = text[start_idx:end_idx].strip()

            # Attempt a rough semester extraction (S1, S2, S3, etc.)
            sem_match = re.search(r"SEMESTER\s*(S\d)", subject_raw_text, re.IGNORECASE)
            semester = sem_match.group(1).upper() if sem_match else "UNKNOWN"

            # Create destination folder paths
            subject_dir = os.path.join(OUTPUT_DIR, category, sub_category, subject_code)
            os.makedirs(subject_dir, exist_ok=True)

            # 1. Save isolated raw text
            with open(os.path.join(subject_dir, "raw.txt"), "w", encoding="utf-8") as f:
                f.write(subject_raw_text)

            # 2. Build and save metadata
            metadata = {
                "subject_code": subject_code,
                "semester": semester,
                "category": category,
                "group_or_branch": sub_category,
                "extraction_status": "pending_minimax"
            }
            
            with open(os.path.join(subject_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)

            # 3. Add to global registry
            all_subjects_registry.append(metadata)
            total_subjects_found += 1

    # Save the global registry mapping
    with open("all_subjects.json", "w", encoding="utf-8") as f:
        json.dump(all_subjects_registry, f, indent=4)

    print(f"\n✅ Pipeline Complete! Successfully isolated {total_subjects_found} subjects.")
    print(f"📁 Check the '{OUTPUT_DIR}' folder and 'all_subjects.json'.")

if __name__ == "__main__":
    build_database()