import os
import requests
import json
import re

SYSTEM_PROMPT = (
    "# SYSTEM OPERATIONAL PROTOCOL: KTU-PREMIER-ENGINE V10\n"
    "ROLE: Senior KTU Board Examiner.\n"
    "OBJECTIVE: Generate premium B.Tech study notes for an ENTIRE MODULE in one go. You must provide detailed notes for EVERY SINGLE TOPIC listed in the prompt.\n\n"
    
    "## STRICT FORMATTING PROTOCOL\n"
    "For EACH topic, you must use this exact structure:\n"
    "### TOPIC: [Exact Topic Name]\n"
    "<!-- SECTION_1_START -->\n... core definition ...\n<!-- SECTION_1_END -->\n"
    "<!-- SECTION_2_START -->\n... deep analysis ...\n<!-- SECTION_2_END -->\n"
    "<!-- SECTION_3_START -->\n... derivations / algorithms ...\n<!-- SECTION_3_END -->\n"
    "<!-- SECTION_4_START -->\n... structural diagrams ...\n<!-- SECTION_4_END -->\n"
    "<!-- SECTION_5_START -->\n... examination questions ...\n<!-- SECTION_5_END -->\n\n"
    "You must repeat this full structure for EVERY topic requested. Do not skip any topic. Do not truncate or summarize. Provide exhaustive detail for each."
)

user_content = (
    "Generate notes for the following 4 topics in 'Module 1: Graph Theory' of 'GAMAT401':\n"
    "1. Introduction to Graphs - Basic Definition\n"
    "2. Directed and Undirected Graphs\n"
    "3. Graph Isomorphism\n"
    "4. Subgraphs\n\n"
    "Ensure you output the full 5-section structure for all 4 topics."
)

def run():
    with open("miniall.txt", "r", encoding="utf-8") as f:
        keys = [k.strip() for k in f.read().split(",") if k.strip()]
    
    if not keys:
        return

    api_key = keys[0]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "MiniMax-M3",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1
    }

    print("Requesting FULL MODULE notes from MiniMax...")
    resp = requests.post("https://api.tokenrouter.com/v1/chat/completions", headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    
    content = data["choices"][0]["message"]["content"]
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    
    output_path = r"C:\Users\Windows 10\.gemini\antigravity\brain\e1633bb6-1fbf-4037-8d91-937705fe5e13\module_test.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Done! Saved to {output_path}")
    print(f"Total Output Tokens (Approx): {len(content.split())}")
    
    topics_found = content.count("### TOPIC:")
    print(f"Topics found in output: {topics_found} / 4")

if __name__ == "__main__":
    run()
