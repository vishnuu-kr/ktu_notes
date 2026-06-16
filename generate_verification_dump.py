import os
import json

data_dir = r"C:\Users\Windows 10\Downloads\ktunode\src\data\subjects"
output_file = r"C:\Users\Windows 10\Downloads\ktu-node-extractor\verification_dump.txt"

def generate_dump():
    total_subjects = 0
    total_topics = 0
    
    with open(output_file, 'w', encoding='utf-8') as out:
        for filename in sorted(os.listdir(data_dir)):
            if not filename.endswith('.json'):
                continue
                
            branch_sem = filename.replace('.json', '')
            out.write(f"=======================================================\n")
            out.write(f"FILE: {filename} (Branch-Sem: {branch_sem.upper()})\n")
            out.write(f"=======================================================\n\n")
            
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                subjects = json.load(f)
                
            for idx, subject in enumerate(subjects):
                total_subjects += 1
                out.write(f"  [{idx+1}] SUBJECT: {subject.get('code')} - {subject.get('name')}\n")
                
                modules = subject.get('modules', [])
                for mod in modules:
                    out.write(f"      MODULE: {mod.get('title')}\n")
                    topics = mod.get('topics', [])
                    for t_idx, topic in enumerate(topics):
                        total_topics += 1
                        out.write(f"         - {topic.get('title')}\n")
                out.write("\n")
                
    print(f"Dump complete! Saved to {output_file}")
    print(f"Total Subjects: {total_subjects}")
    print(f"Total Topics: {total_topics}")

if __name__ == '__main__':
    generate_dump()
