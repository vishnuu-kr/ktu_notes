import requests, json, os

with open("miniall.txt", "r") as f:
    key = f.read().split(",")[0].strip()

url = "https://api.tokenrouter.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {key}"
}
payload = {
    "model": "MiniMax-M3",
    "messages": [
        {"role": "user", "content": "hello"}
    ],
    "temperature": 0.1, 
    "max_tokens": 50
}
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print("STATUS:", resp.status_code)
    print(resp.text)
except Exception as e:
    print("ERROR:", e)