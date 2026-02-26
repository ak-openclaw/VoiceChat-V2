#!/usr/bin/env python3
"""Debug test to find the exact issue"""
import sys
import os

print("="*60)
print("DEBUG TEST")
print("="*60)

# 1. Check backend file exists and has correct routes
print("\n1️⃣ Checking backend/server.py...")
if not os.path.exists("backend/server.py"):
    print("   ❌ backend/server.py NOT FOUND")
    sys.exit(1)

with open("backend/server.py") as f:
    content = f.read()

# Check for FastAPI
if "from fastapi" not in content:
    print("   ❌ Not a FastAPI app")
    sys.exit(1)
print("   ✅ FastAPI app")

# Check routes
routes = []
if '@app.get("/api/health")' in content:
    routes.append("/api/health")
if '@app.post("/api/chat")' in content:
    routes.append("/api/chat")
if '@app.post("/api/voice-chat")' in content:
    routes.append("/api/voice-chat")

print(f"   Found routes: {routes}")

if len(routes) < 3:
    print("   ❌ Missing routes!")
    sys.exit(1)
print("   ✅ All /api routes present")

# 2. Check frontend API service
print("\n2️⃣ Checking frontend/src/services/api.ts...")
if not os.path.exists("frontend/src/services/api.ts"):
    print("   ❌ api.ts NOT FOUND")
    sys.exit(1)

with open("frontend/src/services/api.ts") as f:
    api_content = f.read()

if "'/api'" not in api_content and '"/api"' not in api_content:
    print("   ❌ No /api path in API service")
    sys.exit(1)
if "localhost:9004" in api_content:
    print("   ❌ API service uses localhost:9004 (should use relative URL)")
    sys.exit(1)
print("   ✅ API service uses relative /api URLs")

# 3. Check vite config
print("\n3️⃣ Checking vite.config.ts...")
if not os.path.exists("frontend/vite.config.ts"):
    print("   ❌ vite.config.ts NOT FOUND")
    sys.exit(1)

with open("frontend/vite.config.ts") as f:
    vite_content = f.read()

if "proxy" not in vite_content:
    print("   ❌ No proxy in vite config")
    sys.exit(1)
if "9004" not in vite_content:
    print("   ❌ No port 9004 in vite config")
    sys.exit(1)
print("   ✅ Vite config has proxy to port 9004")

print("\n" + "="*60)
print("✅ ALL CONFIG CHECKS PASSED")
print("="*60)

# 4. Now start backend and test
print("\n4️⃣ Starting backend for testing...")
os.chdir("backend")

import subprocess
import time

# Start backend
proc = subprocess.Popen(
    ["python3", "server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
time.sleep(5)

# Test backend directly
print("\n5️⃣ Testing backend directly...")
import requests
try:
    r = requests.get("http://localhost:9004/api/health", timeout=5)
    print(f"   /api/health: {r.status_code}")
    print(f"   Response: {r.json()}")
    
    if r.status_code != 200:
        print("   ❌ Backend health check failed")
        proc.terminate()
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Backend not responding: {e}")
    proc.terminate()
    sys.exit(1)

# Test voice-chat endpoint
print("\n6️⃣ Testing /api/voice-chat endpoint...")
try:
    dummy_audio = b"RIFF\x00\x00\x00\x00WAVEfmt "
    r = requests.post(
        "http://localhost:9004/api/voice-chat",
        files={"audio": ("test.webm", dummy_audio, "audio/webm")},
        timeout=10
    )
    print(f"   /api/voice-chat: {r.status_code}")
    print(f"   Response: {r.text[:200]}")
    
    if r.status_code == 404:
        print("   ❌ /api/voice-chat returns 404!")
        proc.terminate()
        sys.exit(1)
    elif "error" in r.text.lower():
        print("   ⚠️  Endpoint exists but returned error (expected without OpenAI key)")
    else:
        print("   ✅ Endpoint working")
        
except Exception as e:
    print(f"   ❌ Request failed: {e}")
    proc.terminate()
    sys.exit(1)

proc.terminate()

print("\n" + "="*60)
print("✅ BACKEND TESTS PASSED")
print("="*60)
print("\nAll tests passed. Issue must be with frontend/vite/ngrok.")

