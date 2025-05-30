#!/usr/bin/env python3
"""
Simple test script to verify the Plex Media Renamer web application starts correctly.
"""

import sys
import os
import requests
import time
import subprocess
from threading import Thread

def test_health_endpoint():
    """Test the health endpoint to verify the application is running."""
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('status') == 'healthy':
                    print("✅ Health check passed!")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Version: {data.get('version')}")
                    print(f"   Timestamp: {data.get('timestamp')}")
                    return True
                else:
                    print(f"❌ Health check failed: {data}")
                    return False
            else:
                print(f"❌ Health check failed with status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            if i < max_retries - 1:
                print(f"⏳ Waiting for application to start... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"❌ Failed to connect to application: {e}")
                return False
    return False

def test_main_page():
    """Test that the main page loads correctly."""
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        if response.status_code == 200 and 'Plex Media Renamer' in response.text:
            print("✅ Main page loads correctly!")
            return True
        else:
            print(f"❌ Main page failed: Status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to load main page: {e}")
        return False

def test_config_endpoint():
    """Test the configuration endpoint."""
    try:
        response = requests.get('http://localhost:5000/api/config', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Configuration endpoint working!")
                config = data.get('config', {})
                print(f"   Base media path: {config.get('base_media_path', 'Not set')}")
                print(f"   Dry run mode: {config.get('dry_run_mode', 'Not set')}")
                return True
            else:
                print(f"❌ Configuration endpoint failed: {data}")
                return False
        else:
            print(f"❌ Configuration endpoint failed with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to test configuration endpoint: {e}")
        return False

def run_flask_app():
    """Run the Flask application in a separate thread."""
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import and run the app
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Failed to start Flask application: {e}")

def main():
    """Main test function."""
    print("🧪 Testing Plex Media Renamer Web Application")
    print("=" * 50)
    
    # Start the Flask application in a separate thread
    print("🚀 Starting Flask application...")
    flask_thread = Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    # Wait a moment for the application to start
    time.sleep(3)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    print("\n📋 Running tests...")
    print("-" * 30)
    
    if test_health_endpoint():
        tests_passed += 1
    
    if test_main_page():
        tests_passed += 1
    
    if test_config_endpoint():
        tests_passed += 1
    
    # Summary
    print("\n📊 Test Results")
    print("-" * 30)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The application is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the application setup.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 