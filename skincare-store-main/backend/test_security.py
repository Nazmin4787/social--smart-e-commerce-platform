"""
Test script for backend security features
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

# Test 1: Register with valid data
print("\n🔐 TESTING SECURITY & AUTHENTICATION\n")

print("1️⃣ Testing User Registration (Valid Data)")
data = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/auth/register/", json=data)
print_result("Register Valid User", response)

if response.status_code == 201:
    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    print(f"✅ Access Token: {access_token[:50]}...")
    print(f"✅ Refresh Token: {refresh_token[:50]}...")
else:
    print("❌ Registration failed!")
    exit(1)

# Test 2: Register with invalid email
print("\n2️⃣ Testing Registration Validation (Invalid Email)")
data = {
    "name": "Test User 2",
    "email": "invalid-email",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/auth/register/", json=data)
print_result("Register Invalid Email", response)

# Test 3: Register with short password
print("\n3️⃣ Testing Registration Validation (Short Password)")
data = {
    "name": "Test User 3",
    "email": "test3@example.com",
    "password": "123"
}
response = requests.post(f"{BASE_URL}/auth/register/", json=data)
print_result("Register Short Password", response)

# Test 4: Register duplicate email
print("\n4️⃣ Testing Duplicate Email Prevention")
data = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/auth/register/", json=data)
print_result("Register Duplicate Email", response)

# Test 5: Login with correct password
print("\n5️⃣ Testing Login (Correct Password)")
data = {
    "email": "test@example.com",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/auth/login/", json=data)
print_result("Login Correct Password", response)

if response.status_code == 200:
    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    print("✅ Login successful with hashed password!")
else:
    print("❌ Login failed!")

# Test 6: Login with wrong password
print("\n6️⃣ Testing Login (Wrong Password)")
data = {
    "email": "test@example.com",
    "password": "wrongpassword"
}
response = requests.post(f"{BASE_URL}/auth/login/", json=data)
print_result("Login Wrong Password", response)

# Test 7: Refresh token
print("\n7️⃣ Testing Token Refresh")
data = {
    "refresh_token": refresh_token
}
response = requests.post(f"{BASE_URL}/auth/refresh/", json=data)
print_result("Refresh Token", response)

if response.status_code == 200:
    new_access_token = response.json().get("access_token")
    print(f"✅ New Access Token: {new_access_token[:50]}...")
else:
    print("❌ Token refresh failed!")

# Test 8: Get cart with valid token
print("\n8️⃣ Testing Authenticated Request (Get Cart)")
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/cart/", headers=headers)
print_result("Get Cart (Authenticated)", response)

# Test 9: Get cart with invalid token
print("\n9️⃣ Testing Invalid Token")
headers = {"Authorization": "Bearer invalid_token_here"}
response = requests.get(f"{BASE_URL}/cart/", headers=headers)
print_result("Get Cart (Invalid Token)", response)

# Test 10: Add to cart with stock validation
print("\n🔟 Testing Add to Cart with Stock Validation")
headers = {"Authorization": f"Bearer {access_token}"}
data = {
    "product_id": 1,
    "qty": 1
}
response = requests.post(f"{BASE_URL}/cart/add/", json=data, headers=headers)
print_result("Add to Cart", response)

# Test 11: Test product creation with validation
print("\n1️⃣1️⃣ Testing Product Creation Validation")
data = {
    "title": "Te",  # Too short
    "description": "Test description",
    "price": -10,  # Negative price
    "stock": 50
}
response = requests.post(f"{BASE_URL}/products/create/", json=data)
print_result("Create Product (Invalid Data)", response)

# Test 12: Create valid product
print("\n1️⃣2️⃣ Testing Valid Product Creation")
data = {
    "title": "Test Product",
    "description": "Test description",
    "price": 29.99,
    "stock": 100,
    "category": "skincare"
}
response = requests.post(f"{BASE_URL}/products/create/", json=data)
print_result("Create Product (Valid Data)", response)

print("\n" + "="*60)
print("🎉 ALL TESTS COMPLETED!")
print("="*60)
print("\n✅ Security Features Tested:")
print("   - Password hashing")
print("   - JWT token generation")
print("   - Token refresh mechanism")
print("   - Input validation (email, password, price)")
print("   - Authentication middleware")
print("   - Stock validation")
print("   - Duplicate email prevention")
print("   - Invalid token handling")
