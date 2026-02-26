#!/usr/bin/env python3
"""
Simple Backend Test - No pytest dependency
"""

import sys
import os

# Test 1: Import and route check
print("\n1️⃣ Testing backend imports...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))
    from server import app
    print("   ✅ Backend imports work")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check routes
print("\n2️⃣ Checking routes have /api prefix...")
routes = [route.path for route in app.routes if hasattr(route, 'path')]
api_routes = [r for r in routes if r.startswith('/api/')]

required = ['/api/health', '/api/chat', '/api/voice-chat']
missing = [r for r in required if r not in api_routes]

if missing:
    print(f"   ❌ Missing routes: {missing}")
    print(f"   Found routes: {api_routes}")
    sys.exit(1)
else:
    print(f"   ✅ All required /api routes present: {api_routes}")

# Test 3: FastAPI test client
print("\n3️⃣ Testing with FastAPI TestClient...")
try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    response = client.get("/api/health")
    assert response.status_code == 200, f"Status: {response.status_code}"
    data = response.json()
    assert data.get("status") == "ok", f"Data: {data}"
    print(f"   ✅ /api/health responds: {data}")
    
    # Test chat endpoint exists (will fail due to no OpenAI key, but route exists)
    response = client.post("/api/chat", data={"message": "test"})
    assert response.status_code != 404, "Route not found"
    print(f"   ✅ /api/chat endpoint exists")
    
except Exception as e:
    print(f"   ❌ TestClient failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL BACKEND TESTS PASSED")
print("="*60 + "\n")
sys.exit(0)
