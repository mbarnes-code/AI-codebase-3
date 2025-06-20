#!/usr/bin/env python3

import requests
import json
import time
import sys

def test_api_endpoint(name, url, expected_status=200, timeout=5):
    """Test an API endpoint and return True if successful"""
    try:
        print(f"🔍 Testing {name}: {url}")
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == expected_status:
            print(f"✅ {name}: OK (status {response.status_code})")
            return True
        else:
            print(f"❌ {name}: Failed (status {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: Connection failed - {e}")
        return False

def main():
    print("🧪 Jane AI Platform API Test Suite")
    print("==================================")
    
    # Wait a moment for services to be ready
    print("⏳ Waiting for services to initialize...")
    time.sleep(5)
    
    # Test endpoints
    tests = [
        ("ADHD Support Health", "http://127.0.0.1:8001/health"),
        ("Auth Service Health", "http://127.0.0.1:8003/health"),
        ("MCP Server Tools", "http://127.0.0.1:8002/tools"),
        ("Grafana Health", "http://127.0.0.1:3000/api/health"),
        ("Prometheus Health", "http://127.0.0.1:9090/-/healthy"),
    ]
    
    passed = 0
    failed = 0
    
    for name, url in tests:
        if test_api_endpoint(name, url):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*40)
    print(f"📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All API tests passed!")
        return 0
    else:
        print("⚠️ Some API tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
