"""
Test script for User Management features:
- User Profile (Get/Update)
- Address CRUD (Create, Read, Update, Delete)
- Change Password
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def print_result(test_name, response):
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

# Global variable to store tokens
access_token = None

print("🧪 TESTING USER MANAGEMENT FEATURES\n")

# Test 1: Register a new user
print("1️⃣ Register Test User")
response = requests.post(f"{BASE_URL}/auth/register/", json={
    "name": "Profile Test User",
    "email": "profile@test.com",
    "password": "testpass123"
})
print_result("Register User", response)
if response.status_code == 201:
    access_token = response.json()["access_token"]
    print(f"✅ Access Token: {access_token[:50]}...\n")

# Test 2: Get User Profile
print("2️⃣ Get User Profile")
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/profile/", headers=headers)
print_result("Get Profile", response)

# Test 3: Update User Profile (Change Name)
print("3️⃣ Update User Profile")
response = requests.put(
    f"{BASE_URL}/profile/update/",
    headers=headers,
    json={"name": "Updated Profile Name"}
)
print_result("Update Profile", response)

# Test 4: Update Profile with Invalid Name (Too Short)
print("4️⃣ Update Profile - Validation Error")
response = requests.put(
    f"{BASE_URL}/profile/update/",
    headers=headers,
    json={"name": "A"}
)
print_result("Update Profile Invalid", response)

# Test 5: Create Shipping Address
print("5️⃣ Create Shipping Address")
shipping_address = {
    "address_type": "shipping",
    "full_name": "John Doe",
    "phone": "+1-555-1234",
    "address_line1": "123 Main Street",
    "address_line2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "is_default": True
}
response = requests.post(
    f"{BASE_URL}/addresses/create/",
    headers=headers,
    json=shipping_address
)
print_result("Create Shipping Address", response)
shipping_id = response.json().get("address", {}).get("id") if response.status_code == 201 else None

# Test 6: Create Billing Address
print("6️⃣ Create Billing Address")
billing_address = {
    "address_type": "billing",
    "full_name": "John Doe",
    "phone": "+1-555-5678",
    "address_line1": "456 Oak Avenue",
    "address_line2": "",
    "city": "Los Angeles",
    "state": "CA",
    "postal_code": "90001",
    "country": "USA",
    "is_default": True
}
response = requests.post(
    f"{BASE_URL}/addresses/create/",
    headers=headers,
    json=billing_address
)
print_result("Create Billing Address", response)
billing_id = response.json().get("address", {}).get("id") if response.status_code == 201 else None

# Test 7: Create Address with Invalid Data
print("7️⃣ Create Address - Validation Error")
invalid_address = {
    "address_type": "invalid_type",
    "full_name": "J",  # Too short
    "phone": "123",  # Too short
    "address_line1": "123",  # Too short
    "city": "A",  # Too short
    "state": "C",  # Too short
    "postal_code": "12",  # Too short
    "country": "U"  # Too short
}
response = requests.post(
    f"{BASE_URL}/addresses/create/",
    headers=headers,
    json=invalid_address
)
print_result("Create Invalid Address", response)

# Test 8: Get All Addresses
print("8️⃣ Get All Addresses")
response = requests.get(f"{BASE_URL}/addresses/", headers=headers)
print_result("Get Addresses", response)

# Test 9: Update Shipping Address
if shipping_id:
    print("9️⃣ Update Shipping Address")
    updated_shipping = {
        "address_type": "shipping",
        "full_name": "John Smith",  # Updated name
        "phone": "+1-555-9999",  # Updated phone
        "address_line1": "789 New Street",  # Updated address
        "address_line2": "Suite 100",
        "city": "New York",
        "state": "NY",
        "postal_code": "10002",
        "country": "USA",
        "is_default": True
    }
    response = requests.put(
        f"{BASE_URL}/addresses/{shipping_id}/",
        headers=headers,
        json=updated_shipping
    )
    print_result("Update Address", response)

# Test 10: Delete Billing Address
if billing_id:
    print("🔟 Delete Billing Address")
    response = requests.delete(
        f"{BASE_URL}/addresses/{billing_id}/delete/",
        headers=headers
    )
    print_result("Delete Address", response)

# Test 11: Verify Address Deleted
print("1️⃣1️⃣ Verify Address Deleted")
response = requests.get(f"{BASE_URL}/addresses/", headers=headers)
print_result("Get Addresses After Delete", response)

# Test 12: Change Password - Wrong Old Password
print("1️⃣2️⃣ Change Password - Wrong Old Password")
response = requests.post(
    f"{BASE_URL}/auth/change-password/",
    headers=headers,
    json={
        "old_password": "wrongpassword",
        "new_password": "newpass123"
    }
)
print_result("Change Password Wrong Old", response)

# Test 13: Change Password - Invalid New Password (Too Short)
print("1️⃣3️⃣ Change Password - Invalid New Password")
response = requests.post(
    f"{BASE_URL}/auth/change-password/",
    headers=headers,
    json={
        "old_password": "testpass123",
        "new_password": "short"
    }
)
print_result("Change Password Invalid", response)

# Test 14: Change Password - Same as Old
print("1️⃣4️⃣ Change Password - Same as Old")
response = requests.post(
    f"{BASE_URL}/auth/change-password/",
    headers=headers,
    json={
        "old_password": "testpass123",
        "new_password": "testpass123"
    }
)
print_result("Change Password Same", response)

# Test 15: Change Password - Success
print("1️⃣5️⃣ Change Password - Success")
response = requests.post(
    f"{BASE_URL}/auth/change-password/",
    headers=headers,
    json={
        "old_password": "testpass123",
        "new_password": "newpass123"
    }
)
print_result("Change Password Success", response)

# Test 16: Login with New Password
print("1️⃣6️⃣ Login with New Password")
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "profile@test.com",
    "password": "newpass123"
})
print_result("Login New Password", response)

# Test 17: Login with Old Password (Should Fail)
print("1️⃣7️⃣ Login with Old Password (Should Fail)")
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "profile@test.com",
    "password": "testpass123"
})
print_result("Login Old Password", response)

print("\n" + "="*60)
print("🎉 ALL USER MANAGEMENT TESTS COMPLETED!")
print("="*60)

print("""
✅ Features Tested:
   - Get user profile
   - Update user profile with validation
   - Create shipping address
   - Create billing address
   - Address validation (phone, postal code, etc.)
   - Get all addresses
   - Update address
   - Delete address
   - Change password validation
   - Password verification (old password check)
   - New password validation
   - Login with new password
""")
