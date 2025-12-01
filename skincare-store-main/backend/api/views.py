import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .utils import create_jwt, create_refresh_token, decode_jwt
from .models import Product, AppUser, Cart, CartItem, Order, OrderItem, Address, UserLikedProduct
from .validators import (
    validate_user_registration, 
    validate_product_data, 
    sanitize_string,
    validate_quantity,
    validate_address_data,
    validate_password,
    validate_name
)


def jsonify_python(obj, status=200):
    return JsonResponse(obj, safe=False, status=status)


def list_products(request):
    prods = [p.to_dict() for p in Product.objects.all()]
    return jsonify_python(prods)


def get_product(request, product_id):
    try:
        p = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    return jsonify_python(p.to_dict())


@csrf_exempt
def create_product(request):
    if request.method != "POST":
        return HttpResponseBadRequest()
    body = json.loads(request.body)
    
    # Validate product data
    valid, errors = validate_product_data(body)
    if not valid:
        return JsonResponse({"error": "Validation failed", "details": errors}, status=400)
    
    # Sanitize inputs
    title = sanitize_string(body.get("title"), max_length=255)
    description = sanitize_string(body.get("description", ""), max_length=5000)
    category = sanitize_string(body.get("category", "general"), max_length=100)
    
    p = Product.objects.create(
        title=title,
        description=description,
        price=body.get("price", 0),
        stock=int(body.get("stock", 0)),
        images=body.get("images", []),
        category=category,
    )
    return JsonResponse({"id": p.id, "message": "Product created successfully"}, status=201)


@csrf_exempt
def register(request):
    if request.method != "POST":
        return HttpResponseBadRequest()
    body = json.loads(request.body)
    
    # Validate registration data
    valid, errors = validate_user_registration(body)
    if not valid:
        return JsonResponse({"error": "Validation failed", "details": errors}, status=400)
    
    email = body.get("email").strip().lower()
    
    # Check if user exists
    if AppUser.objects.filter(email=email).exists():
        return JsonResponse({"error": "User with this email already exists"}, status=400)
    
    # Create user with hashed password
    user = AppUser.objects.create(
        name=sanitize_string(body.get("name"), max_length=200),
        email=email,
    )
    user.set_password(body.get("password"))
    user.save()
    
    # Create empty cart
    Cart.objects.create(user=user)
    
    # Generate tokens
    token_payload = {"user_id": user.id, "email": user.email}
    access_token = create_jwt(token_payload)
    refresh_token = create_refresh_token(token_payload)
    
    return JsonResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }, status=201)


@csrf_exempt
def login(request):
    if request.method != "POST":
        return HttpResponseBadRequest()
    body = json.loads(request.body)
    
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    
    if not email or not password:
        return JsonResponse({"error": "Email and password are required"}, status=400)
    
    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Invalid email or password"}, status=401)
    
    # Use password hashing check
    if not user.check_password(password):
        return JsonResponse({"error": "Invalid email or password"}, status=401)
    
    # Generate tokens
    token_payload = {"user_id": user.id, "email": user.email}
    access_token = create_jwt(token_payload)
    refresh_token = create_refresh_token(token_payload)
    
    return JsonResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    })


@csrf_exempt
def add_to_cart(request):
    if request.method != "POST":
        return HttpResponseBadRequest()
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    # Check for token errors
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    body = json.loads(request.body)
    user_id = data["user_id"]
    
    # Validate quantity
    qty = body.get("qty", 1)
    valid, msg = validate_quantity(qty)
    if not valid:
        return JsonResponse({"error": msg}, status=400)
    
    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    cart, _ = Cart.objects.get_or_create(user=user)
    
    try:
        product = Product.objects.get(pk=body["product_id"])
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    
    # Check stock availability
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    new_qty = int(qty) if created else item.qty + int(qty)
    
    if new_qty > product.stock:
        return JsonResponse({
            "error": f"Insufficient stock. Only {product.stock} items available"
        }, status=400)
    
    item.qty = new_qty
    item.save()
    
    return JsonResponse({"ok": True, "message": "Item added to cart"})


def get_cart(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    # Check for token errors
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    user_id = data["user_id"]
    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    cart, _ = Cart.objects.get_or_create(user=user)
    items = []
    for it in cart.items.select_related('product').all():
        items.append({
            'product': it.product.to_dict(),
            'qty': it.qty,
        })
    return jsonify_python(items)


@csrf_exempt
def create_order(request):
    if request.method != "POST":
        return HttpResponseBadRequest()
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    # Check for token errors
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    body = json.loads(request.body)
    user_id = data["user_id"]
    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    # Validate order items and check stock
    items = body.get('items', [])
    if not items:
        return JsonResponse({"error": "Order must contain at least one item"}, status=400)
    
    # Check stock for all items
    for it in items:
        try:
            prod = Product.objects.get(pk=it['product']['id'])
            if prod.stock < it.get('qty', 1):
                return JsonResponse({
                    "error": f"Insufficient stock for {prod.title}. Only {prod.stock} available"
                }, status=400)
        except Product.DoesNotExist:
            return JsonResponse({"error": f"Product not found"}, status=404)
    
    order = Order.objects.create(user=user, total=body.get('total', 0))
    
    # Create order items and reduce stock
    for it in items:
        prod = Product.objects.get(pk=it['product']['id'])
        OrderItem.objects.create(
            order=order, 
            product=prod, 
            qty=it.get('qty', 1), 
            price=prod.price
        )
        # Reduce stock
        prod.stock -= it.get('qty', 1)
        prod.save()
    
    # Clear cart
    CartItem.objects.filter(cart__user=user).delete()
    
    return JsonResponse({
        "order_id": order.id, 
        "message": "Order created successfully"
    }, status=201)


@csrf_exempt
def refresh_token(request):
    """Refresh access token using refresh token."""
    if request.method != "POST":
        return HttpResponseBadRequest()
    
    body = json.loads(request.body)
    refresh = body.get("refresh_token", "")
    
    if not refresh:
        return JsonResponse({"error": "Refresh token is required"}, status=400)
    
    data = decode_jwt(refresh)
    
    # Check for token errors
    if not data or "error" in data:
        error_msg = data.get("error", "Invalid refresh token") if data else "Invalid refresh token"
        return JsonResponse({"error": error_msg}, status=401)
    
    # Verify it's a refresh token
    if data.get("type") != "refresh":
        return JsonResponse({"error": "Invalid token type"}, status=401)
    
    # Generate new access token
    token_payload = {"user_id": data["user_id"], "email": data["email"]}
    new_access_token = create_jwt(token_payload)
    
    return JsonResponse({"access_token": new_access_token})


# USER PROFILE ENDPOINTS

def get_user_profile(request):
    """Get current user profile."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
        return JsonResponse(user.to_dict())
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


@csrf_exempt
def update_user_profile(request):
    """Update current user profile (name and bio, email is immutable)."""
    if request.method != "PUT":
        return HttpResponseBadRequest()
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    body = json.loads(request.body)
    
    # Validate name if provided
    if "name" in body:
        name = body.get("name", "").strip()
        valid, msg = validate_name(name)
        if not valid:
            return JsonResponse({"error": msg}, status=400)
        user.name = sanitize_string(name, max_length=200)
    
    # Update bio if provided
    if "bio" in body:
        bio = body.get("bio", "").strip()
        user.bio = sanitize_string(bio, max_length=1000)
    
    user.save()
    
    return JsonResponse({
        "message": "Profile updated successfully",
        "user": user.to_dict()
    })


# ADDRESS ENDPOINTS

def get_addresses(request):
    """Get all addresses for current user."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
        addresses = [addr.to_dict() for addr in user.addresses.all().order_by('-is_default', '-created_at')]
        return JsonResponse(addresses, safe=False)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


@csrf_exempt
def create_address(request):
    """Create a new address for current user."""
    if request.method != "POST":
        return HttpResponseBadRequest()
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    body = json.loads(request.body)
    
    # Validate address data
    valid, errors = validate_address_data(body)
    if not valid:
        return JsonResponse({"error": "Validation failed", "details": errors}, status=400)
    
    # Handle default address logic
    is_default = body.get('is_default', False)
    if is_default:
        # Remove default from other addresses of same type
        Address.objects.filter(
            user=user, 
            address_type=body['address_type']
        ).update(is_default=False)
    
    # Create address
    address = Address.objects.create(
        user=user,
        address_type=body['address_type'],
        full_name=sanitize_string(body['full_name'], max_length=200),
        phone=sanitize_string(body['phone'], max_length=20),
        address_line1=sanitize_string(body['address_line1'], max_length=255),
        address_line2=sanitize_string(body.get('address_line2', ''), max_length=255),
        city=sanitize_string(body['city'], max_length=100),
        state=sanitize_string(body['state'], max_length=100),
        postal_code=sanitize_string(body['postal_code'], max_length=20),
        country=sanitize_string(body.get('country', 'USA'), max_length=100),
        is_default=is_default
    )
    
    return JsonResponse({
        "message": "Address created successfully",
        "address": address.to_dict()
    }, status=201)


@csrf_exempt
def update_address(request, address_id):
    """Update an existing address."""
    if request.method != "PUT":
        return HttpResponseBadRequest()
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
        address = Address.objects.get(pk=address_id, user=user)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Address.DoesNotExist:
        return JsonResponse({"error": "Address not found"}, status=404)
    
    body = json.loads(request.body)
    
    # Validate address data
    valid, errors = validate_address_data(body)
    if not valid:
        return JsonResponse({"error": "Validation failed", "details": errors}, status=400)
    
    # Handle default address logic
    is_default = body.get('is_default', False)
    if is_default and not address.is_default:
        # Remove default from other addresses of same type
        Address.objects.filter(
            user=user, 
            address_type=body['address_type']
        ).exclude(pk=address_id).update(is_default=False)
    
    # Update address
    address.address_type = body['address_type']
    address.full_name = sanitize_string(body['full_name'], max_length=200)
    address.phone = sanitize_string(body['phone'], max_length=20)
    address.address_line1 = sanitize_string(body['address_line1'], max_length=255)
    address.address_line2 = sanitize_string(body.get('address_line2', ''), max_length=255)
    address.city = sanitize_string(body['city'], max_length=100)
    address.state = sanitize_string(body['state'], max_length=100)
    address.postal_code = sanitize_string(body['postal_code'], max_length=20)
    address.country = sanitize_string(body.get('country', 'USA'), max_length=100)
    address.is_default = is_default
    address.save()
    
    return JsonResponse({
        "message": "Address updated successfully",
        "address": address.to_dict()
    })


@csrf_exempt
def delete_address(request, address_id):
    """Delete an address."""
    if request.method != "DELETE":
        return HttpResponseBadRequest()
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
        address = Address.objects.get(pk=address_id, user=user)
        address.delete()
        return JsonResponse({"message": "Address deleted successfully"})
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Address.DoesNotExist:
        return JsonResponse({"error": "Address not found"}, status=404)


# PASSWORD CHANGE ENDPOINT

@csrf_exempt
def change_password(request):
    """Change user password."""
    if request.method != "POST":
        return HttpResponseBadRequest()
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    body = json.loads(request.body)
    old_password = body.get("old_password", "")
    new_password = body.get("new_password", "")
    
    # Verify old password
    if not user.check_password(old_password):
        return JsonResponse({"error": "Current password is incorrect"}, status=400)
    
    # Validate new password
    valid, msg = validate_password(new_password)
    if not valid:
        return JsonResponse({"error": msg}, status=400)
    
    # Ensure new password is different from old
    if old_password == new_password:
        return JsonResponse({"error": "New password must be different from current password"}, status=400)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return JsonResponse({"message": "Password changed successfully"})


# MY ORDERS ENDPOINT

def get_my_orders(request):
    """Get all orders for current user with order items."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
        orders = Order.objects.filter(user=user).prefetch_related('items__product').order_by('-created_at')
        
        orders_data = []
        for order in orders:
            order_items = []
            for item in order.items.all():
                order_items.append({
                    'product': item.product.to_dict(),
                    'qty': item.qty,
                    'price': float(item.price)
                })
            
            orders_data.append({
                'id': order.id,
                'total': float(order.total),
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'items': order_items
            })
        
        return JsonResponse(orders_data, safe=False)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


# LIKED PRODUCTS ENDPOINTS

def get_liked_products(request):
    """Get all liked products for current user."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
        liked = UserLikedProduct.objects.filter(user=user).select_related('product')
        liked_data = [lp.to_dict() for lp in liked]
        return JsonResponse(liked_data, safe=False)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


@csrf_exempt
def like_product(request):
    """Add a product to user's liked products."""
    if request.method != "POST":
        return HttpResponseBadRequest()
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    body = json.loads(request.body)
    product_id = body.get("product_id")
    
    if not product_id:
        return JsonResponse({"error": "Product ID is required"}, status=400)
    
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    
    # Check if already liked
    if UserLikedProduct.objects.filter(user=user, product=product).exists():
        return JsonResponse({"error": "Product already liked"}, status=400)
    
    # Create liked product
    liked = UserLikedProduct.objects.create(user=user, product=product)
    
    return JsonResponse({
        "message": "Product added to favorites",
        "liked": liked.to_dict()
    }, status=201)


@csrf_exempt
def unlike_product(request, product_id):
    """Remove a product from user's liked products."""
    if request.method != "DELETE":
        return HttpResponseBadRequest()
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)
    
    try:
        user = AppUser.objects.get(pk=data["user_id"])
        liked = UserLikedProduct.objects.get(user=user, product_id=product_id)
        liked.delete()
        return JsonResponse({"message": "Product removed from favorites"})
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except UserLikedProduct.DoesNotExist:
        return JsonResponse({"error": "Product not in favorites"}, status=404)


# ABOUT US ENDPOINT

def about_us(request):
    """Get about us information."""
    about_data = {
        "company_name": "Skincare Store",
        "description": "Your trusted destination for premium skincare products. We believe in natural beauty and provide high-quality products to help you achieve healthy, glowing skin.",
        "mission": "To provide accessible, effective skincare solutions that enhance natural beauty and promote skin health.",
        "founded": "2024",
        "contact": {
            "email": "support@skincarestore.com",
            "phone": "+1-800-SKINCARE",
            "address": "123 Beauty Lane, Wellness City, CA 90210"
        },
        "social_media": {
            "instagram": "@skincarestore",
            "facebook": "facebook.com/skincarestore",
            "twitter": "@skincarestore"
        }
    }
    return JsonResponse(about_data)
