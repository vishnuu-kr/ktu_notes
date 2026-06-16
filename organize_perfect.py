import os
import json
import shutil

DB_DIR = 'database'
PERFECT_DIR = 'perfect'

def organize_perfect():
    if os.path.exists(PERFECT_DIR):
        shutil.rmtree(PERFECT_DIR)
    os.makedirs(PERFECT_DIR)
    
    # code -> list of dicts: {'path', 'branch', 'meta', 'struct', 'content_hash'}
    subjects = {}
    
    for root, dirs, files in os.walk(DB_DIR):
        if 'structured.json' not in files:
            continue
        
        # Skip references
        if 'reference.json' in files:
            continue
            
        code = os.path.basename(root)
        
        meta = {}
        if 'metadata.json' in files:
            with open(os.path.join(root, 'metadata.json'), 'r', encoding='utf-8') as f:
                meta = json.load(f)
                
        with open(os.path.join(root, 'structured.json'), 'r', encoding='utf-8') as f:
            struct = json.load(f)
            
        content_str = json.dumps(struct, sort_keys=True)
        branch = meta.get('group_or_branch', 'Unknown')
        name = meta.get('subject_name', '')
        
        if code not in subjects:
            subjects[code] = []
            
        subjects[code].append({
            'path': root,
            'branch': branch,
            'name': name,
            'meta': meta,
            'struct': struct,
            'content_str': content_str
        })
        
    print(f"Found {len(subjects)} unique subject codes.")
    
    same_content_count = 0
    diff_content_count = 0
    
    for code, entries in subjects.items():
        # Clean subject name for folder
        name = entries[0]['name'].strip()
        # safe folder name
        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        
        folder_name = f"{code}"
        if safe_name:
            folder_name += f" - {safe_name}"
            
        subject_dir = os.path.join(PERFECT_DIR, folder_name)
        os.makedirs(subject_dir, exist_ok=True)
        
        unique_contents = {}
        for entry in entries:
            content = entry['content_str']
            if content not in unique_contents:
                unique_contents[content] = []
            unique_contents[content].append(entry)
            
        if len(unique_contents) == 1:
            same_content_count += 1
            # Just one version
            out_struct = os.path.join(subject_dir, 'structured.json')
            out_meta = os.path.join(subject_dir, 'metadata.json')
            
            with open(out_struct, 'w', encoding='utf-8') as f:
                json.dump(entries[0]['struct'], f, indent=4, ensure_ascii=False)
                
            combined_meta = entries[0]['meta'].copy()
            combined_meta['branches'] = [e['branch'] for e in entries]
            if 'group_or_branch' in combined_meta:
                del combined_meta['group_or_branch']
                
            with open(out_meta, 'w', encoding='utf-8') as f:
                json.dump(combined_meta, f, indent=4, ensure_ascii=False)
        else:
            diff_content_count += 1
            # Multiple versions
            for content, group_entries in unique_contents.items():
                branches_str = "_".join([e['branch'] for e in group_entries])
                # Cap length of filename
                if len(branches_str) > 50:
                    branches_str = branches_str[:47] + "..."
                    
                prefix = branches_str
                
                out_struct = os.path.join(subject_dir, f'{prefix}_structured.json')
                with open(out_struct, 'w', encoding='utf-8') as f:
                    json.dump(group_entries[0]['struct'], f, indent=4, ensure_ascii=False)
                    
                out_meta = os.path.join(subject_dir, f'{prefix}_metadata.json')
                combined_meta = group_entries[0]['meta'].copy()
                combined_meta['branches'] = [e['branch'] for e in group_entries]
                if 'group_or_branch' in combined_meta:
                    del combined_meta['group_or_branch']
                    
                with open(out_meta, 'w', encoding='utf-8') as f:
                    json.dump(combined_meta, f, indent=4, ensure_ascii=False)
                    
    print(f"Subjects with identical content across all branches: {same_content_count}")
    print(f"Subjects with different variations across branches: {diff_content_count}")
    print(f"All files have been cleanly organized into the '{PERFECT_DIR}/' folder.")

if __name__ == '__main__':
    organize_perfect()
