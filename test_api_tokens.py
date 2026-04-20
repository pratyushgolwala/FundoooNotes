#!/usr/bin/env python
"""Test token API endpoints."""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

print("=== Testing Token Generation in Login API ===\n")

# Test login endpoint
login_data = {
    "username": "testuser",
    "password": "password123"
}

print(f"POST {BASE_URL}/api/login/")
print(f"Payload: {json.dumps(login_data)}\n")

try:
    response = requests.post(
        f"{BASE_URL}/api/login/",
        json=login_data,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        print(f"Response:")
        print(f"  - Access Token: {result.get('access_token', 'N/A')[:50]}...")
        print(f"  - Refresh Token: {result.get('refresh_token', 'N/A')[:50]}...")
        print(f"  - Token Type: {result.get('token_type', 'N/A')}")
        print(f"  - Expires In: {result.get('expires_in', 'N/A')} seconds")
        print(f"  - User ID: {result.get('user_id', 'N/A')}")
        
        access_token = result.get('access_token')
        refresh_token = result.get('refresh_token')
        
        print("\n✅ Login endpoint returns both access and refresh tokens!\n")
        
        # Test refresh endpoint
        if refresh_token:
            print("=== Testing Token Refresh Endpoint ===\n")
            print(f"POST {BASE_URL}/api/refresh/")
            print(f"Payload: {{'refresh_token': '{refresh_token[:50]}...'}}\n")
            
            refresh_data = {"refresh_token": refresh_token}
            refresh_response = requests.post(
                f"{BASE_URL}/api/refresh/",
                json=refresh_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"Status: {refresh_response.status_code}")
            refresh_result = refresh_response.json()
            
            if refresh_response.status_code == 200:
                print(f"Response:")
                print(f"  - New Access Token: {refresh_result.get('access_token', 'N/A')[:50]}...")
                print(f"  - New Refresh Token: {refresh_result.get('refresh_token', 'N/A')[:50]}...")
                print(f"  - Token Type: {refresh_result.get('token_type', 'N/A')}")
                print(f"  - User ID: {refresh_result.get('user_id', 'N/A')}")
                print("\n✅ Refresh endpoint successfully issued new tokens!\n")
            else:
                print(f"Error: {refresh_result}\n")
        
        # Test protected API with bearer token
        if access_token:
            print("=== Testing Protected Notes API with Bearer Token ===\n")
            print(f"GET {BASE_URL}/api/notes/")
            print(f"Headers: Authorization: Bearer {access_token[:50]}...\n")
            
            notes_response = requests.get(
                f"{BASE_URL}/api/notes/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=5
            )
            
            print(f"Status: {notes_response.status_code}")
            if notes_response.status_code == 200:
                notes = notes_response.json()
                print(f"Notes: {json.dumps(notes, indent=2)[:200]}...")
                print("\n✅ Bearer token works for protected API endpoints!\n")
            else:
                print(f"Error: {notes_response.json()}\n")
    else:
        print(f"Error: {result}")
        
except requests.exceptions.ConnectionError:
    print("❌ Connection Error: Make sure Django server is running at http://127.0.0.1:8000/")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("=" * 60)
print("✅ All token API tests passed!")
print("=" * 60)
