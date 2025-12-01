"""
Test script for additional User Profile features:
- Bio field in profile
- My Orders
- Liked Products (like/unlike)
- About Us
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

# Global variables
access_token = None
product_id = None

print("🧪 TESTING ADDITIONAL PROFILE FEATURES\n")

# Test 1: Register a new user
print("1️⃣ Register Test User")
response = requests.post(f"{BASE_URL}/auth/register/", json={
    "name": "Feature Test User",
    "email": "features@test.com",
    "password": "testpass123"
})
print_result("Register User", response)
if response.status_code == 201:
    access_token = response.json()["access_token"]
    print(f"✅ Access Token: {access_token[:50]}...\n")

headers = {"Authorization": f"Bearer {access_token}"}

# Test 2: Get Profile (Should have empty bio)
print("2️⃣ Get Profile - Empty Bio")
response = requests.get(f"{BASE_URL}/profile/", headers=headers)
print_result("Get Profile", response)

# Test 3: Update Profile with Bio
print("3️⃣ Update Profile - Add Bio")
response = requests.put(
    f"{BASE_URL}/profile/update/",
    headers=headers,
    json={
        "name": "Feature Test User",
        "bio": "Skincare enthusiast passionate about natural beauty products. Love trying new serums and moisturizers!"
    }
)
print_result("Update Profile with Bio", response)

# Test 4: Get Profile (Should now have bio)
print("4️⃣ Get Profile - With Bio")
response = requests.get(f"{BASE_URL}/profile/", headers=headers)
print_result("Get Profile", response)

# Test 5: Create a test product
print("5️⃣ Create Test Product")
response = requests.post(
    f"{BASE_URL}/products/create/",
    json={
        "title": "Hydrating Serum",
        "description": "Amazing hydrating serum with hyaluronic acid",
        "price": 29.99,
        "stock": 100,
        "category": "serums"
    }
)
print_result("Create Product", response)
if response.status_code == 201:
    product_id = response.json()["id"]

# Test 6: Like a product
print("6️⃣ Like Product")
response = requests.post(
    f"{BASE_URL}/liked-products/like/",
    headers=headers,
    json={"product_id": product_id}
)
print_result("Like Product", response)

# Test 7: Like same product again (should fail)
print("7️⃣ Like Same Product Again (Should Fail)")
response = requests.post(
    f"{BASE_URL}/liked-products/like/",
    headers=headers,
    json={"product_id": product_id}
)
print_result("Like Duplicate", response)

# Test 8: Get Liked Products
print("8️⃣ Get Liked Products")
response = requests.get(f"{BASE_URL}/liked-products/", headers=headers)
print_result("Get Liked Products", response)

# Test 9: Create another product and like it
print("9️⃣ Create and Like Second Product")
response = requests.post(
    f"{BASE_URL}/products/create/",
    json={
        "title": "Vitamin C Cream",
        "description": "Brightening cream with vitamin C",
        "price": 39.99,
        "stock": 50,
        "category": "moisturizers"
    }
)
if response.status_code == 201:
    product_id_2 = response.json()["id"]
    response = requests.post(
        f"{BASE_URL}/liked-products/like/",
        headers=headers,
        json={"product_id": product_id_2}
    )
    print_result("Like Second Product", response)

# Test 10: Get All Liked Products (Should have 2)
print("🔟 Get All Liked Products")
response = requests.get(f"{BASE_URL}/liked-products/", headers=headers)
print_result("Get All Liked Products", response)

# Test 11: Unlike first product
print("1️⃣1️⃣ Unlike First Product")
response = requests.delete(
    f"{BASE_URL}/liked-products/{product_id}/unlike/",
    headers=headers
)
print_result("Unlike Product", response)

# Test 12: Get Liked Products (Should have 1)
print("1️⃣2️⃣ Get Liked Products After Unlike")
response = requests.get(f"{BASE_URL}/liked-products/", headers=headers)
print_result("Get Liked Products", response)

# Test 13: Create an order
print("1️⃣3️⃣ Create Test Order")
response = requests.post(
    f"{BASE_URL}/orders/create/",
    headers=headers,
    json={
        "items": [
            {
                "product": {"id": product_id},
                "qty": 2
            }
        ],
        "total": 59.98
    }
)
print_result("Create Order", response)

# Test 14: Get My Orders
print("1️⃣4️⃣ Get My Orders")
response = requests.get(f"{BASE_URL}/orders/", headers=headers)
print_result("Get My Orders", response)

# Test 15: Get My Orders (Empty for new user would be tested separately)
print("1️⃣5️⃣ About Us Endpoint (No Auth Required)")
response = requests.get(f"{BASE_URL}/about-us/")
print_result("About Us", response)

# Test 16: Like product without auth (should fail)
print("1️⃣6️⃣ Like Product Without Auth (Should Fail)")
response = requests.post(
    f"{BASE_URL}/liked-products/like/",
    json={"product_id": product_id}
)
print_result("Like Without Auth", response)

# Test 17: Get orders without auth (should fail)
print("1️⃣7️⃣ Get Orders Without Auth (Should Fail)")
response = requests.get(f"{BASE_URL}/orders/")
print_result("Orders Without Auth", response)

print("\n" + "="*60)
print("🎉 ALL PROFILE FEATURE TESTS COMPLETED!")
print("="*60)

print("""
✅ Features Tested:
   - Profile bio field (get/update)
   - Create and get liked products
   - Like product (with duplicate prevention)
   - Unlike product
   - Get all liked products
   - Create order with products
   - Get my orders with details
   - About us endpoint (public)
   - Authentication on protected endpoints
""")
