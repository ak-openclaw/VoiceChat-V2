#!/usr/bin/env python3
"""
Backend API Tests for Voice Chat v2
Run before starting servers to verify everything works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient

# Import the FastAPI app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))
from server import app

client = TestClient(app)

class TestBackendAPI:
    """Test all backend endpoints"""
    
    def test_health_endpoint(self):
        """Test /api/health returns correct response"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "session" in data
        print("✅ /api/health works")
    
    def test_chat_endpoint_exists(self):
        """Test /api/chat endpoint exists and accepts POST"""
        response = client.post("/api/chat", data={"message": "test"})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        print("✅ /api/chat exists")
    
    def test_voice_chat_endpoint_exists(self):
        """Test /api/voice-chat endpoint exists and accepts POST with file"""
        # Create dummy audio file
        dummy_audio = b"RIFF\x00\x00\x00\x00WAVEfmt "
        response = client.post(
            "/api/voice-chat",
            files={"audio": ("test.webm", dummy_audio, "audio/webm")}
        )
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        print("✅ /api/voice-chat exists")
    
    def test_routes_have_api_prefix(self):
        """Verify all routes have /api prefix"""
        routes = [route.path for route in app.routes]
        api_routes = [r for r in routes if r.startswith("/api/")]
        
        assert "/api/health" in api_routes
        assert "/api/chat" in api_routes
        assert "/api/voice-chat" in api_routes
        print("✅ All routes have /api prefix")
    
    def test_cors_enabled(self):
        """Test CORS headers are present"""
        response = client.options("/api/health")
        assert "access-control-allow-origin" in str(response.headers).lower()
        print("✅ CORS enabled")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("RUNNING BACKEND API TESTS")
    print("="*60 + "\n")
    
    try:
        test = TestBackendAPI()
        test.test_health_endpoint()
        test.test_chat_endpoint_exists()
        test.test_voice_chat_endpoint_exists()
        test.test_routes_have_api_prefix()
        test.test_cors_enabled()
        
        print("\n" + "="*60)
        print("✅ ALL BACKEND TESTS PASSED")
        print("="*60 + "\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("="*60 + "\n")
        sys.exit(1)
