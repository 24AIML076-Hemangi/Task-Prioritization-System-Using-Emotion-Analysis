import requests
import json

BASE_URL = "http://localhost:5000/api/auth"

print("\n" + "="*60)
print("🧪 COMPREHENSIVE AUTH FLOW TEST")
print("="*60)

# Test 1: Signup new user
print("\n1️⃣  SIGNUP TEST")
print("-" * 60)
new_user = {"email": "test@example.com", "password": "TestPass123"}
response = requests.post(f"{BASE_URL}/signup", json=new_user)
print(f"   Email: {new_user['email']}")
print(f"   Status: {response.status_code}")
if response.ok:
    print(f"   ✅ User created: {response.json()}")
else:
    print(f"   ❌ Error: {response.json()}")

# Test 2: Try duplicate signup (should fail)
print("\n2️⃣  DUPLICATE SIGNUP TEST (Should fail)")
print("-" * 60)
response = requests.post(f"{BASE_URL}/signup", json=new_user)
print(f"   Status: {response.status_code}")
if not response.ok:
    print(f"   ✅ Correctly rejected: {response.json()['error']}")
else:
    print(f"   ❌ Should have failed!")

# Test 3: Login with correct credentials
print("\n3️⃣  LOGIN TEST (Correct credentials)")
print("-" * 60)
login_data = {"email": "john@test.com", "password": "password123"}
response = requests.post(f"{BASE_URL}/login", json=login_data)
print(f"   Email: {login_data['email']}")
print(f"   Status: {response.status_code}")
if response.ok:
    user = response.json()['user']
    print(f"   ✅ Login successful")
    print(f"      - User ID: {user['id']}")
    print(f"      - Email: {user['email']}")
else:
    print(f"   ❌ Login failed: {response.json()}")

# Test 4: Login with wrong password
print("\n4️⃣  LOGIN TEST (Wrong password)")
print("-" * 60)
login_data = {"email": "john@test.com", "password": "wrongpassword"}
response = requests.post(f"{BASE_URL}/login", json=login_data)
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   ✅ Correctly rejected: {response.json()['error']}")
else:
    print(f"   ❌ Should have rejected!")

# Test 5: Login with non-existent user
print("\n5️⃣  LOGIN TEST (Non-existent user)")
print("-" * 60)
login_data = {"email": "nouser@test.com", "password": "anything"}
response = requests.post(f"{BASE_URL}/login", json=login_data)
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   ✅ Correctly rejected: {response.json()['error']}")
else:
    print(f"   ❌ Should have rejected!")

print("\n" + "="*60)
print("✅ ALL TESTS COMPLETED")
print("="*60 + "\n")
