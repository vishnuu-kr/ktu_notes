import ai_refiner
import time
import os

PERFECT_DIR = "perfect"

while True:
    ai_refiner.processed_count = 0
    ai_refiner.process_all()
    
    # Check completion
    total = len([d for d in os.listdir(PERFECT_DIR) if os.path.isdir(os.path.join(PERFECT_DIR, d))])
    
    completed = 0
    for root, dirs, files in os.walk(PERFECT_DIR):
        if "ai_perfect.json" in files:
            completed += 1
            
    print(f"Total completed: {completed}/{total}")
    if completed >= total:
        print("ALL DONE!")
        break
        
    print("Sleeping for 30 seconds before retrying...")
    time.sleep(30)
