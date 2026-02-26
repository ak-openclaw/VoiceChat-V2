#!/usr/bin/env python3
"""
Simple Frontend Integration Test
"""

import os
import sys
import requests

def test_file(filepath, checks):
    """Test a file exists and contains required strings"""
    print(f"\n📄 Testing {filepath}...")
    
    if not os.path.exists(filepath):
        print(f"   ❌ File not found: {filepath}")
        return False
    
    with open(filepath) as f:
        content = f.read()
    
    for name, check in checks.items():
        should_exist = not check.startswith("NOT:")
        search_term = check.replace("NOT:", "")
        
        if should_exist:
            if search_term not in content:
                print(f"   ❌ Missing: {name} ({search_term})")
                return False
            print(f"   ✅ Has {name}")
        else:
            if search_term in content:
                print(f"   ❌ Should NOT have: {name} ({search_term})")
                return False
            print(f"   ✅ Correctly does NOT have {name}")
    
    return True

# Run tests
print("="*60)
print("FRONTEND CONFIGURATION TESTS")
print("="*60)

all_passed = True

# Test 1: Vite config
if not test_file("frontend/vite.config.ts", {
    "proxy": "proxy",
    "api path": "'/api'",
    "backend port": "9004"
}):
    all_passed = False

# Test 2: API service
if not test_file("frontend/src/services/api.ts", {
    "relative API path": "'/api'",
    "absolute URL": "NOT:localhost:9004"
}):
    all_passed = False

# Test 3: Backend routes
if not test_file("backend/server.py", {
    "/api/health": '"/api/health"',
    "/api/chat": '"/api/chat"',
    "/api/voice-chat": '"/api/voice-chat"'
}):
    all_passed = False

# Summary
print("\n" + "="*60)
if all_passed:
    print("✅ ALL CONFIGURATION TESTS PASSED")
    print("="*60 + "\n")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")
    sys.exit(1)
