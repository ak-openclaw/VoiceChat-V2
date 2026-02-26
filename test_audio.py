import sys
sys.path.insert(0, 'backend')
import os
os.chdir('backend')

from server import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test chat endpoint
print("Testing /api/chat...")
response = client.post("/api/chat", data={"message": "hello"})
data = response.json()
print(f"  Status: {response.status_code}")
print(f"  Has audio: {'audio' in data}")
print(f"  Audio length: {len(data.get('audio', '')) if data.get('audio') else 0}")
print(f"  Response text: {data.get('text', '')[:50]}")
