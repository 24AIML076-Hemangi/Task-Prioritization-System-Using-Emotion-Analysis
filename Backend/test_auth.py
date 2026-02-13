import requests
import json

# Flask is running on localhost:5000
BASE_URL = "http://localhost:5000/api/auth"

test_users = [
    {"email": "john@test.com", "password": "password123"},
    {"email": "jane@test.com", "password": "securePass456"}
]

print("\n=== CREATING TEST USERS ===\n")

for user in test_users:
    response = requests.post(f"{BASE_URL}/signup", json=user)
    print(f"📝 Signup: {user['email']}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

print("\n=== TESTING LOGIN ===\n")

for user in test_users:
    response = requests.post(f"{BASE_URL}/login", json=user)
    print(f"🔐 Login: {user['email']}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

print("\n=== TESTING LOGIN WITH WRONG PASSWORD ===\n")

response = requests.post(f"{BASE_URL}/login", json={"email": "john@test.com", "password": "wrongpassword"})
print(f"❌ Wrong password:")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}\n")
