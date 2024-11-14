import requests
import json

def test_chat_api(query: str):
    url = "http://127.0.0.1:5002/ask"
    
    payload = {
        "query": query,
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json().get('answer')
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    r = test_chat_api(query="Tell me about artificial intelligence") 
    print(r)