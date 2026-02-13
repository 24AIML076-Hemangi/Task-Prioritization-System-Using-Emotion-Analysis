import requests
import json

BASE_URL = "http://localhost:5000/api/auth"

print("\n" + "="*60)
print("🔐 PASSWORD RESET FLOW TEST")
print("="*60)

# Test user
test_email = "john@test.com"
test_old_password = "password123"
test_new_password = "NewPassword123"

# Step 1: Request password reset
print("\n1️⃣  FORGOT PASSWORD REQUEST")
print("-" * 60)
response = requests.post(f"{BASE_URL}/forgot-password", json={"email": test_email})
print(f"   Email: {test_email}")
print(f"   Status: {response.status_code}")

if response.ok:
    data = response.json()
    reset_code = None
    print(f"   ✅ Reset code sent")
    print(f"   Message: {data.get('message')}")
    
    # Extract reset code from console output or use a mock code
    # For testing, we'll need to manually check what code was generated
    # Let's just use a test code that we know will exist
    reset_code = "000000"  # Will be replaced with actual code
else:
    print(f"   ❌ Error: {response.json()}")
    exit()

# For this test, we'll assume the code was sent and manually enter it
# In a real scenario, the code would be sent via email and user would provide it
print("\n   📌 Enter the 6-digit code from console output above:")
print("   (For testing, the code is printed to console when reset is requested)")

# Manual test: verify code
# Note: Since we don't have access to the actual code printed to console,
# we'll demonstrate the flow with placeholder values

print("\n2️⃣  VERIFY RESET CODE")
print("-" * 60)
# This step would use the actual code from the email/console
print("   (Code verification would happen here)")
print("   (Requires actual reset code from console output)")

# Step 3: Reset password
print("\n3️⃣  RESET PASSWORD")
print("-" * 60)
print("   Note: This requires the actual 6-digit code from step 1")
print("   For manual testing:")
print("   - Check the console where Flask is running for the reset code")
print("   - Then run the password reset with the actual code")

# Step 4: Test login with new password
print("\n4️⃣  LOGIN WITH NEW PASSWORD")
print("-" * 60)
print("   After resetting password, you can login with:")
print(f"   Email: {test_email}")
print(f"   Password: {test_new_password}")

print("\n" + "="*60)
print("✅ PASSWORD RESET FLOW READY FOR MANUAL TEST")
print("="*60)
print("\nINSTRUCTIONS FOR MANUAL TEST:")
print("1. Run this script (see code printed above)")
print("2. Check Flask console for the 6-digit reset code")
print("3. Use that code to verify and reset password")
print("4. Login with new password to confirm")
print()
