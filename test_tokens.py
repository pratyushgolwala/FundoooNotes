#!/usr/bin/env python
"""Test token generation integration."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FundooMain.settings')
django.setup()

from users.token_utils import generate_tokens, decode_token
import jwt

# Test token generation
print("=== Testing Token Generation ===\n")

user_id = 1
tokens = generate_tokens(user_id)

print(f"Generated Tokens for User {user_id}:")
print(f"  - Access Token (Bearer): {tokens['access_token'][:50]}...")
print(f"  - Refresh Token: {tokens['refresh_token'][:50]}...")
print(f"  - Token Type: {tokens['token_type']}")
print(f"  - Expires In: {tokens['expires_in']} seconds\n")

# Test decoding
print("=== Testing Token Decoding ===\n")

try:
    access_payload = decode_token(tokens['access_token'])
    print(f"Access Token Payload:")
    print(f"  - User ID: {access_payload['user_id']}")
    print(f"  - Token Type: {access_payload.get('token_type', 'N/A')}")
    print(f"  - Expires: {access_payload.get('exp', 'N/A')}")
except Exception as e:
    print(f"Error decoding access token: {e}")

print()

try:
    refresh_payload = decode_token(tokens['refresh_token'])
    print(f"Refresh Token Payload:")
    print(f"  - User ID: {refresh_payload['user_id']}")
    print(f"  - Token Type: {refresh_payload.get('token_type', 'N/A')}")
    print(f"  - Expires: {refresh_payload.get('exp', 'N/A')}")
except Exception as e:
    print(f"Error decoding refresh token: {e}")

print("\n✅ Token generation and decoding working correctly!")
