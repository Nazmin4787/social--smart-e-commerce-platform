import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from .utils import create_jwt, create_refresh_token, decode_jwt
from .models import (
    Product,
    AppUser,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Address,
    UserLikedProduct,
    Booking,
    Review,
    Banner,
)
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
    
    # Check if request has files (multipart/form-data)
    if request.FILES:
        # Handle file upload
        title = request.POST.get("title", "")
        description = request.POST.get("description", "")
        price = request.POST.get("price", 0)
        stock = request.POST.get("stock", 0)
        category = request.POST.get("category", "general")
        
        # Sanitize inputs
        title = sanitize_string(title, max_length=255)
        description = sanitize_string(description, max_length=5000)
        category = sanitize_string(category, max_length=100)
        
        # Handle image uploads
        images = []
        uploaded_files = request.FILES.getlist('images')
        
        if uploaded_files:
            import os
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            # Create products directory if it doesn't exist
            products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
            os.makedirs(products_dir, exist_ok=True)
            
            for uploaded_file in uploaded_files:
                # Generate unique filename
                import uuid
                ext = uploaded_file.name.split('.')[-1]
                filename = f"{uuid.uuid4()}.{ext}"
                filepath = os.path.join('products', filename)
                
                # Save the file
                saved_path = default_storage.save(filepath, uploaded_file)
                
                # Store the URL (accessible via MEDIA_URL)
                image_url = f"{settings.MEDIA_URL}{saved_path}"
                images.append(image_url)
        
        p = Product.objects.create(
            title=title,
            description=description,
            price=float(price) if price else 0,
            stock=int(stock) if stock else 0,
            images=images,
            category=category,
        )
        return JsonResponse({"id": p.id, "message": "Product created successfully"}, status=201)
    else:
        # Handle JSON data (backward compatibility)
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
def update_cart_item(request):
    if request.method != "POST" and request.method != "PUT":
        return HttpResponseBadRequest()
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)

    body = json.loads(request.body)
    user_id = data["user_id"]

    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    cart, _ = Cart.objects.get_or_create(user=user)
    product_id = body.get('product_id')
    qty = int(body.get('qty', 1))
    if not product_id:
        return JsonResponse({"error": "product_id is required"}, status=400)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    try:
        item = CartItem.objects.get(cart=cart, product=product)
        if qty <= 0:
            item.delete()
            return JsonResponse({"message": "Item removed from cart"})
        if qty > product.stock:
            return JsonResponse({"error": f"Insufficient stock. Only {product.stock} available"}, status=400)
        item.qty = qty
        item.save()
        return JsonResponse({"message": "Cart updated"})
    except CartItem.DoesNotExist:
        if qty <= 0:
            return JsonResponse({"error": "Item not in cart"}, status=404)
        # create new
        if qty > product.stock:
            return JsonResponse({"error": f"Insufficient stock. Only {product.stock} available"}, status=400)
        CartItem.objects.create(cart=cart, product=product, qty=qty)
        return JsonResponse({"message": "Item added to cart"}, status=201)


@csrf_exempt
def remove_cart_item(request, product_id):
    if request.method != "DELETE":
        return HttpResponseBadRequest()
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)

    user_id = data["user_id"]
    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    cart, _ = Cart.objects.get_or_create(user=user)
    try:
        item = CartItem.objects.get(cart=cart, product_id=product_id)
        item.delete()
        return JsonResponse({"message": "Item removed from cart"})
    except CartItem.DoesNotExist:
        return JsonResponse({"error": "Item not found in cart"}, status=404)


@csrf_exempt
def create_booking(request):
    if request.method != "POST":
        return HttpResponseBadRequest()

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)

    body = json.loads(request.body)
    user_id = data["user_id"]

    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    product_id = body.get('product_id')
    if not product_id:
        return JsonResponse({"error": "product_id is required"}, status=400)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    qty = int(body.get('qty', 1))
    if qty < 1:
        return JsonResponse({"error": "Quantity must be at least 1"}, status=400)

    # Optionally check stock when confirming payment
    delivery_date = body.get('delivery_date')
    notes = body.get('notes', '')
    payment_status = body.get('payment_status', 'pending')

    booking = Booking.objects.create(
        user=user,
        product=product,
        qty=qty,
        payment_status=payment_status,
        notes=notes,
        delivery_date=delivery_date if delivery_date else None,
        status='confirmed' if payment_status == 'paid' else 'pending'
    )

    # If paid, optionally reduce stock
    if booking.payment_status == 'paid' and product.stock >= booking.qty:
        product.stock -= booking.qty
        product.save()

    return JsonResponse({"booking": booking.to_dict(), "message": "Booking created"}, status=201)


def get_bookings(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)

    user_id = data["user_id"]
    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    bookings = Booking.objects.filter(user=user).select_related('product').order_by('-booking_date')
    return JsonResponse([b.to_dict() for b in bookings], safe=False)


def get_booking(request, booking_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)

    user_id = data["user_id"]
    try:
        booking = Booking.objects.select_related('product', 'user').get(pk=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found"}, status=404)

    if booking.user.id != user_id:
        return JsonResponse({"error": "Forbidden"}, status=403)

    return JsonResponse(booking.to_dict())


@csrf_exempt
def add_review(request, product_id):
    if request.method != "POST":
        return HttpResponseBadRequest()

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = decode_jwt(token)
    if not data or "error" in data:
        error_msg = data.get("error", "Unauthorized") if data else "Unauthorized"
        return JsonResponse({"error": error_msg}, status=401)

    user_id = data["user_id"]
    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    body = json.loads(request.body)
    rating = int(body.get('rating', 5))
    comment = body.get('comment', '')

    if rating < 1 or rating > 5:
        return JsonResponse({"error": "Rating must be between 1 and 5"}, status=400)

    review = Review.objects.create(user=user, product=product, rating=rating, comment=comment)
    return JsonResponse({"review": review.to_dict(), "message": "Review added"}, status=201)


def get_reviews(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    reviews = product.reviews.select_related('user').all().order_by('-created_at')
    return JsonResponse([r.to_dict() for r in reviews], safe=False)


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


@csrf_exempt
def toggle_like_product(request):
    """Toggle like status for a product (like if not liked, unlike if already liked)."""
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
    liked_product = UserLikedProduct.objects.filter(user=user, product=product).first()
    
    if liked_product:
        # Unlike - remove from favorites
        liked_product.delete()
        return JsonResponse({
            "message": "Product removed from favorites",
            "liked": False
        })
    else:
        # Like - add to favorites
        liked = UserLikedProduct.objects.create(user=user, product=product)
        return JsonResponse({
            "message": "Product added to favorites",
            "liked": True,
            "data": liked.to_dict()
        }, status=201)


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


# BANNERS
def get_banners(request):
    """Public endpoint to fetch active banners ordered by position."""
    banners = Banner.objects.filter(is_active=True).order_by('position', '-created_at')
    data = [b.to_dict(request=request) for b in banners]
    return JsonResponse(data, safe=False)


# ADMIN: Products list with pagination and filters
def admin_products_list(request):
    user, err = _require_admin(request)
    if err:
        return err

    qs = Product.objects.all()

    # Filters
    category = request.GET.get('category')
    if category:
        qs = qs.filter(category__iexact=category)

    stock_status = request.GET.get('stock_status')  # in_stock, out_of_stock, all
    if stock_status == 'in_stock':
        qs = qs.filter(stock__gt=0)
    elif stock_status == 'out_of_stock':
        qs = qs.filter(stock__lte=0)

    try:
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        if price_min is not None:
            qs = qs.filter(price__gte=float(price_min))
        if price_max is not None:
            qs = qs.filter(price__lte=float(price_max))
    except Exception:
        return JsonResponse({'error': 'Invalid price_min or price_max'}, status=400)

    # Pagination
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
    except Exception:
        return JsonResponse({'error': 'Invalid page or page_size'}, status=400)
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size

    products = [p.to_dict() for p in qs.order_by('-id')[start:end]]

    return JsonResponse({'total': total, 'page': page, 'page_size': page_size, 'results': products}, safe=False)


@csrf_exempt
def admin_update_product_stock(request, product_id):
    """Update single product stock (PATCH/POST). JSON: {"stock": <int>}"""
    if request.method not in ('PATCH', 'POST', 'PUT'):
        return HttpResponseBadRequest()

    user, err = _require_admin(request)
    if err:
        return err

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    try:
        body = json.loads(request.body)
    except Exception:
        return HttpResponseBadRequest()

    if 'stock' not in body:
        return JsonResponse({'error': 'stock is required'}, status=400)
    try:
        new_stock = int(body.get('stock'))
    except Exception:
        return JsonResponse({'error': 'stock must be an integer'}, status=400)

    if new_stock < 0:
        return JsonResponse({'error': 'stock must be >= 0'}, status=400)

    product.stock = new_stock
    product.save()
    return JsonResponse({'message': 'Stock updated', 'product_id': product.id, 'stock': product.stock})


@csrf_exempt
def admin_bulk_update_stock(request):
    """Bulk update stocks. Accepts JSON list: [{"id": <product_id>, "stock": <int>}, ...]"""
    if request.method != 'POST':
        return HttpResponseBadRequest()

    user, err = _require_admin(request)
    if err:
        return err

    try:
        body = json.loads(request.body)
    except Exception:
        return HttpResponseBadRequest()

    if not isinstance(body, list):
        return JsonResponse({'error': 'Expected a list of updates'}, status=400)

    results = {'updated': [], 'errors': []}
    for entry in body:
        pid = entry.get('id')
        if pid is None:
            results['errors'].append({'entry': entry, 'error': 'missing id'})
            continue
        try:
            stock_val = int(entry.get('stock'))
        except Exception:
            results['errors'].append({'id': pid, 'error': 'invalid stock'})
            continue
        if stock_val < 0:
            results['errors'].append({'id': pid, 'error': 'stock must be >=0'})
            continue
        try:
            prod = Product.objects.get(pk=pid)
            prod.stock = stock_val
            prod.save()
            results['updated'].append({'id': pid, 'stock': prod.stock})
        except Product.DoesNotExist:
            results['errors'].append({'id': pid, 'error': 'not found'})

    return JsonResponse(results)


@csrf_exempt
def admin_product_update(request, product_id):
    """Admin endpoint to update a product. Supports both JSON and multipart/form-data."""
    if request.method not in ('PUT', 'POST'):
        return HttpResponseBadRequest()

    user, err = _require_admin(request)
    if err:
        return err

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    # Check if request has files (multipart/form-data)
    if request.FILES:
        # Handle file upload
        title = request.POST.get("title")
        description = request.POST.get("description")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        category = request.POST.get("category")
        
        if title:
            product.title = sanitize_string(title, max_length=255)
        if description is not None:
            product.description = sanitize_string(description, max_length=5000)
        if price:
            product.price = float(price)
        if stock is not None:
            product.stock = int(stock)
        if category:
            product.category = sanitize_string(category, max_length=100)
        
        # Handle new image uploads
        uploaded_files = request.FILES.getlist('images')
        if uploaded_files:
            import os
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            # Create products directory if it doesn't exist
            products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
            os.makedirs(products_dir, exist_ok=True)
            
            # Keep existing images and add new ones
            new_images = list(product.images) if product.images else []
            
            for uploaded_file in uploaded_files:
                # Generate unique filename
                import uuid
                ext = uploaded_file.name.split('.')[-1]
                filename = f"{uuid.uuid4()}.{ext}"
                filepath = os.path.join('products', filename)
                
                # Save the file
                saved_path = default_storage.save(filepath, uploaded_file)
                
                # Store the URL
                image_url = f"{settings.MEDIA_URL}{saved_path}"
                new_images.append(image_url)
            
            product.images = new_images
        
        product.save()
        return JsonResponse({'id': product.id, 'message': 'Product updated successfully'})
    else:
        # Handle JSON data
        try:
            body = json.loads(request.body)
        except Exception:
            return HttpResponseBadRequest()

        if 'title' in body:
            product.title = sanitize_string(body['title'], max_length=255)
        if 'description' in body:
            product.description = sanitize_string(body['description'], max_length=5000)
        if 'price' in body:
            product.price = float(body['price'])
        if 'stock' in body:
            product.stock = int(body['stock'])
        if 'category' in body:
            product.category = sanitize_string(body['category'], max_length=100)
        if 'images' in body:
            product.images = body['images']

        product.save()
        return JsonResponse({'id': product.id, 'message': 'Product updated successfully'})


@csrf_exempt
def admin_product_delete(request, product_id):
    """Admin endpoint to delete a product."""
    if request.method != 'DELETE':
        return HttpResponseBadRequest()

    user, err = _require_admin(request)
    if err:
        return err

    try:
        product = Product.objects.get(pk=product_id)
        product.delete()
        return JsonResponse({'message': 'Product deleted successfully'})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


@csrf_exempt
def admin_orders(request):
    """Admin endpoint to list orders with optional filters: status, date_from, date_to, customer."""
    user, err = _require_admin(request)
    if err:
        return err

    qs = Order.objects.select_related('user').prefetch_related('items__product').all()

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    customer = request.GET.get('customer')
    if customer:
        qs = qs.filter(
            models.Q(user__name__icontains=customer) | models.Q(user__email__icontains=customer)
        )

    result = []
    for o in qs.order_by('-created_at'):
        items = []
        for it in o.items.all():
            items.append({'product': it.product.to_dict(), 'qty': it.qty, 'price': float(it.price)})

        # shipping address
        addr = None
        addrobj = Address.objects.filter(user=o.user).order_by('-is_default', '-created_at').first()
        if addrobj:
            addr = {
                'full_name': addrobj.full_name,
                'phone': addrobj.phone,
                'address_line1': addrobj.address_line1,
                'address_line2': addrobj.address_line2,
                'city': addrobj.city,
                'state': addrobj.state,
                'postal_code': addrobj.postal_code,
                'country': addrobj.country,
            }

        result.append({
            'id': o.id,
            'user': {'id': o.user.id, 'name': o.user.name, 'email': o.user.email},
            'total': float(o.total),
            'status': o.status,
            'created_at': o.created_at.isoformat(),
            'items': items,
            'shipping_address': addr,
        })

    return JsonResponse(result, safe=False)


@csrf_exempt
def admin_update_order_status(request, order_id):
    """Admin endpoint to update order status. PATCH with JSON {"status":"..."}"""
    if request.method not in ('PATCH', 'POST'):
        return HttpResponseBadRequest()

    user, err = _require_admin(request)
    if err:
        return err

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

    try:
        body = json.loads(request.body)
    except Exception:
        return HttpResponseBadRequest()

    new_status = body.get('status')
    if not new_status:
        return JsonResponse({'error': 'status is required'}, status=400)

    allowed = ('pending', 'processing', 'shipped', 'delivered', 'cancelled')
    if new_status not in allowed:
        return JsonResponse({'error': f'status must be one of {allowed}'}, status=400)

    order.status = new_status
    order.save()
    return JsonResponse({'message': 'Order status updated', 'order_id': order.id, 'status': order.status})


def admin_dashboard(request):
    """Return basic dashboard statistics: total products, total orders, total revenue."""
    user, err = _require_admin(request)
    if err:
        return err

    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    revenue_agg = Order.objects.aggregate(total=models.Sum('total'))
    revenue = float(revenue_agg.get('total') or 0)

    return JsonResponse({
        'total_products': total_products,
        'total_orders': total_orders,
        'revenue': revenue,
    })


def admin_recent_orders(request):
    """Return a short list of recent orders (with user and total). Query param `limit`."""
    user, err = _require_admin(request)
    if err:
        return err

    try:
        limit = int(request.GET.get('limit', 5))
    except Exception:
        limit = 5

    qs = Order.objects.select_related('user').order_by('-created_at')[:limit]
    out = []
    for o in qs:
        out.append({
            'id': o.id,
            'user': {'id': o.user.id, 'name': o.user.name, 'email': o.user.email} if o.user else None,
            'total': float(o.total),
            'status': o.status,
            'created_at': o.created_at.isoformat(),
        })
    return JsonResponse(out, safe=False)


def admin_low_stock(request):
    """Return products at or below stock threshold. Query param `threshold` (default 5)."""
    user, err = _require_admin(request)
    if err:
        return err

    try:
        threshold = int(request.GET.get('threshold', 5))
    except Exception:
        return JsonResponse({'error': 'threshold must be integer'}, status=400)

    prods = Product.objects.filter(stock__lte=threshold).order_by('stock')[:100]
    out = [{'id': p.id, 'title': p.title, 'stock': p.stock, 'price': float(p.price)} for p in prods]
    return JsonResponse({'threshold': threshold, 'count': len(out), 'results': out})


def admin_top_selling(request):
    """Return top selling products by quantity sold. Query param `limit` (default 10)."""
    user, err = _require_admin(request)
    if err:
        return err

    try:
        limit = int(request.GET.get('limit', 10))
    except Exception:
        limit = 10

    # Aggregate OrderItem quantities by product id
    sales = OrderItem.objects.values('product').annotate(total_qty=models.Sum('qty')).order_by('-total_qty')[:limit]
    product_ids = [s['product'] for s in sales]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    out = []
    for s in sales:
        pid = s['product']
        p = products.get(pid)
        out.append({
            'product_id': pid,
            'title': p.title if p else None,
            'total_qty': int(s['total_qty'] or 0),
        })

    return JsonResponse({'results': out}, safe=False)


def _require_admin(request):
    # Use the IsAdminUser permission helper to centralize admin checks
    from .permissions import IsAdminUser
    perm = IsAdminUser()
    if not perm.has_permission(request):
        # Determine whether unauthorized (no/invalid token) or forbidden (not admin)
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        data = decode_jwt(token)
        if not data or "error" in data:
            return None, JsonResponse({"error": "Unauthorized"}, status=401)
        return None, JsonResponse({"error": "Forbidden"}, status=403)

    user = perm.get_user(request)
    if not user:
        return None, JsonResponse({"error": "Unauthorized"}, status=401)
    return user, None


@csrf_exempt
def admin_banners(request):
    """Admin CRUD for banners. Methods:
    - GET: list all banners
    - POST: create banner (supports multipart form for image)
    - PUT: update banner (JSON body, image update not supported via PUT)
    - DELETE: delete banner (JSON with id)
    """
    user, err = _require_admin(request)
    if err:
        return err

    # List
    if request.method == 'GET':
        banners = Banner.objects.all().order_by('position', '-created_at')
        return JsonResponse([b.to_dict(request=request) for b in banners], safe=False)

    # Create (supports multipart/form-data with `image` file)
    if request.method == 'POST':
        # try to read multipart fields first
        title = None
        link = ''
        is_active = True
        position = 0
        if request.content_type.startswith('multipart/'):
            title = request.POST.get('title')
            link = request.POST.get('link', '')
            is_active = request.POST.get('is_active', 'true').lower() in ('1', 'true', 'yes')
            try:
                position = int(request.POST.get('position', 0))
            except Exception:
                position = 0
            image = request.FILES.get('image')
        else:
            try:
                body = json.loads(request.body)
            except Exception:
                return HttpResponseBadRequest()
            title = body.get('title')
            link = body.get('link', '')
            is_active = bool(body.get('is_active', True))
            position = int(body.get('position', 0))
            image = None

        if not title:
            return JsonResponse({"error": "title is required"}, status=400)

        banner = Banner.objects.create(
            title=title,
            link=link,
            is_active=is_active,
            position=position
        )
        if image:
            # validate image
            from .validators import validate_image_file, optimize_image_file
            valid, err = validate_image_file(image)
            if not valid:
                banner.delete()
                return JsonResponse({"error": err}, status=400)

            optimized = optimize_image_file(image)
            if optimized is not None:
                banner.image = optimized
            else:
                # fallback to original
                banner.image = image
            banner.save()

        return JsonResponse({"message": "Banner created", "banner": banner.to_dict(request=request)}, status=201)

    # Update (PUT) - expects JSON body with 'id'
    if request.method == 'PUT':
        try:
            body = json.loads(request.body)
        except Exception:
            return HttpResponseBadRequest()
        banner_id = body.get('id')
        if not banner_id:
            return JsonResponse({"error": "id is required"}, status=400)
        try:
            banner = Banner.objects.get(pk=banner_id)
        except Banner.DoesNotExist:
            return JsonResponse({"error": "Banner not found"}, status=404)

        if 'title' in body:
            banner.title = body.get('title')
        if 'link' in body:
            banner.link = body.get('link')
        if 'is_active' in body:
            banner.is_active = bool(body.get('is_active'))
        if 'position' in body:
            try:
                banner.position = int(body.get('position', banner.position))
            except Exception:
                pass

        banner.save()
        return JsonResponse({"message": "Banner updated", "banner": banner.to_dict(request=request)})

    # Delete
    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
        except Exception:
            return HttpResponseBadRequest()
        banner_id = body.get('id')
        if not banner_id:
            return JsonResponse({"error": "id is required"}, status=400)
        try:
            banner = Banner.objects.get(pk=banner_id)
            banner.delete()
            return JsonResponse({"message": "Banner deleted"})
        except Banner.DoesNotExist:
            return JsonResponse({"error": "Banner not found"}, status=404)

    return HttpResponseBadRequest()
