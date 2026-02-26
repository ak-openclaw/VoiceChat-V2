#!/usr/bin/env python3
"""
Frontend Integration Tests for Voice Chat v2
Tests the frontend can communicate with backend through Vite proxy
"""

import subprocess
import time
import sys
import os
import requests

def check_port(port, name):
    """Check if a port is responding"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=2)
        print(f"  ✅ {name} (port {port}): Responding")
        return True
    except:
        print(f"  ❌ {name} (port {port}): Not responding")
        return False

class TestFrontendIntegration:
    """Test frontend integration"""
    
    def test_vite_config_exists(self):
        """Verify vite.config.ts exists and has proxy config"""
        config_path = "frontend/vite.config.ts"
        assert os.path.exists(config_path), f"{config_path} not found"
        
        with open(config_path) as f:
            content = f.read()
            assert "proxy" in content, "Vite proxy config missing"
            assert "'/api'" in content or '"/api"' in content, "API proxy path missing"
            assert "9004" in content, "Backend port (9004) missing from proxy"
        
        print("✅ Vite config has proxy settings")
    
    def test_api_service_uses_relative_urls(self):
        """Verify API service uses relative URLs, not absolute"""
        api_path = "frontend/src/services/api.ts"
        assert os.path.exists(api_path), f"{api_path} not found"
        
        with open(api_path) as f:
            content = f.read()
            # Should use relative URLs
            assert "'/api'" in content or '"/api"' in content, "Relative API path missing"
            # Should NOT use localhost in URLs
            assert "localhost:9004" not in content, "API service should NOT use localhost:9004"
        
        print("✅ API service uses relative URLs")
    
    def test_backend_routes_have_api_prefix(self):
        """Verify backend routes have /api prefix"""
        server_path = "backend/server.py"
        assert os.path.exists(server_path), f"{server_path} not found"
        
        with open(server_path) as f:
            content = f.read()
            # Check for /api prefix in routes
            assert '@app.get("/api/health")' in content or "@app.get('/api/health')" in content, "/api/health route missing"
            assert '@app.post("/api/chat")' in content or "@app.post('/api/chat')" in content, "/api/chat route missing"
            assert '@app.post("/api/voice-chat")' in content or "@app.post('/api/voice-chat')" in content, "/api/voice-chat route missing"
        
        print("✅ Backend routes have /api prefix")
    
    def test_servers_running(self):
        """Test that both backend and frontend are running"""
        backend_ok = check_port(9004, "Backend")
        frontend_ok = check_port(5173, "Frontend")
        
        assert backend_ok, "Backend not running on port 9004"
        assert frontend_ok, "Frontend not running on port 5173"
        print("✅ Both servers running")
    
    def test_proxy_integration(self):
        """Test that Vite proxy forwards /api to backend"""
        try:
            # Frontend should proxy /api/health to backend
            response = requests.get("http://localhost:5173/api/health", timeout=5)
            assert response.status_code == 200, f"Proxy failed: {response.status_code}"
            data = response.json()
            assert data.get("status") == "ok", "Backend health check failed"
            print("✅ Vite proxy working (frontend → backend)")
        except Exception as e:
            print(f"  ❌ Proxy test failed: {e}")
            raise


if __name__ == "__main__":
    print("\n" + "="*60)
    print("RUNNING FRONTEND INTEGRATION TESTS")
    print("="*60 + "\n")
    
    # Change to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        test = TestFrontendIntegration()
        test.test_vite_config_exists()
        test.test_api_service_uses_relative_urls()
        test.test_backend_routes_have_api_prefix()
        test.test_servers_running()
        test.test_proxy_integration()
        
        print("\n" + "="*60)
        print("✅ ALL FRONTEND TESTS PASSED")
        print("="*60 + "\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("="*60 + "\n")
        sys.exit(1)
