import requests
import base64

BASE_URL = "http://localhost:5000/api"

print("\n" + "="*60)
print("🧪 EMOTION DETECTION TEST")
print("="*60)

# Create a simple test image (small base64 data)
# For testing, we'll just send a small valid JPEG header
test_image_base64 = """/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDA=="""

test_data = {
    "image": test_image_base64,
    "user_id": "john@test.com"
}

print("\n1️⃣  EMOTION SCAN TEST")
print("-" * 60)
response = requests.post(f"{BASE_URL}/tasks/emotion-scan", json=test_data)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

if response.ok:
    data = response.json()
    print(f"\n   ✅ Emotion Detection Working!")
    print(f"      Emotion: {data['emotion']}")
    print(f"      Confidence: {data['confidence']}")
    print(f"      Message: {data['message']}")

print("\n" + "="*60)
print("✅ EMOTION TEST COMPLETE")
print("="*60 + "\n")
