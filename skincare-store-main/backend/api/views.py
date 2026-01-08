import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.http.multipartparser import MultiPartParser
from rest_framework.decorators import api_view
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
    UserFollow,
    Notification,
    ProductShare,
    Wallet,
    WalletTransaction,
    Payment,
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
from .permissions import IsRegularUser


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
    
    # Check content type to determine how to handle the request
    # Use content_type instead of checking request.FILES directly to avoid reading the stream
    is_multipart = request.content_type and 'multipart/form-data' in request.content_type
    
    if is_multipart or request.POST:
        # Handle file upload or form data
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
        uploaded_files = request.FILES.getlist('images') if request.FILES else []
        
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
        
        # Parse dates
        from datetime import datetime
        expiry_date = None
        manufacturing_date = None
        expiry_str = request.POST.get("expiry_date", "")
        mfg_str = request.POST.get("manufacturing_date", "")
        if expiry_str:
            try:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        if mfg_str:
            try:
                manufacturing_date = datetime.strptime(mfg_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        p = Product.objects.create(
            title=title,
            description=description,
            price=float(price) if price else 0,
            stock=int(stock) if stock else 0,
            images=images,
            category=category,
            is_trending=request.POST.get("is_trending") == "true",
            ingredients=[i.strip() for i in request.POST.get("ingredients", "").split('\n') if i.strip()],
            benefits=[b.strip() for b in request.POST.get("benefits", "").split('\n') if b.strip()],
            how_to_use=[h.strip() for h in request.POST.get("how_to_use", "").split('\n') if h.strip()],
            faqs=json.loads(request.POST.get("faqs", "[]")),
            expiry_date=expiry_date,
            manufacturing_date=manufacturing_date,
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
            is_trending=body.get("is_trending", False),
            ingredients=[i.strip() for i in body.get("ingredients", []) if isinstance(i, str) and i.strip()],
            benefits=[b.strip() for b in body.get("benefits", []) if isinstance(b, str) and b.strip()],
            how_to_use=[h.strip() for h in body.get("how_to_use", []) if isinstance(h, str) and h.strip()],
            faqs=body.get("faqs", []),
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
        allergies=body.get("allergies", [])
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
    
    # Block admin user from shopping
    try:
        user = AppUser.objects.get(pk=user_id)
        if user.is_staff and user.is_superuser:
            return JsonResponse({"error": "Admin users cannot add items to cart."}, status=403)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
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
        if user.is_staff and user.is_superuser:
            return JsonResponse({"error": "Admin users cannot create bookings."}, status=403)
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
        if user.is_staff and user.is_superuser:
            return JsonResponse({"error": "Admin users cannot add reviews."}, status=403)
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
    
    # Invalidate recommendation cache
    from .recommender import invalidate_user_recommendation_cache
    invalidate_user_recommendation_cache(user.id)
    
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
        if user.is_staff and user.is_superuser:
            return JsonResponse({"error": "Admin users cannot create orders."}, status=403)
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
        if user.is_staff and user.is_superuser:
            return JsonResponse({"error": "Admin users cannot like products."}, status=403)
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
    
    # Invalidate recommendation cache
    from .recommender import invalidate_user_recommendation_cache
    invalidate_user_recommendation_cache(user.id)
    
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
        
        # Invalidate recommendation cache
        from .recommender import invalidate_user_recommendation_cache
        invalidate_user_recommendation_cache(user.id)
        
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
        
        # Invalidate recommendation cache
        from .recommender import invalidate_user_recommendation_cache
        invalidate_user_recommendation_cache(user.id)
        
        return JsonResponse({
            "message": "Product removed from favorites",
            "liked": False
        })
    else:
        # Like - add to favorites
        liked = UserLikedProduct.objects.create(user=user, product=product)
        
        # Invalidate recommendation cache
        from .recommender import invalidate_user_recommendation_cache
        invalidate_user_recommendation_cache(user.id)
        
        return JsonResponse({
            "message": "Product added to favorites",
            "liked": True,
            "data": liked.to_dict()
        }, status=201)


# ABOUT US ENDPOINT

def about_us(request):
    """Get about us information."""
    about_data = {
        "company_name": "Novacell",
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
    print(f"[admin_product_update] Called with method={request.method}, product_id={product_id}")
    if request.method not in ('PUT', 'POST'):
        return HttpResponseBadRequest()

    user, err = _require_admin(request)
    if err:
        print(f"[admin_product_update] Auth error: {err}")
        return err

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        print(f"[admin_product_update] Product {product_id} not found")
        return JsonResponse({'error': 'Product not found'}, status=404)

    print(f"[admin_product_update] Content-Type: {request.content_type}")
    
    # Check if request has multipart/form-data content type
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Django doesn't parse multipart for PUT by default, so we do it manually
        if request.method == 'PUT':
            parser = MultiPartParser(request.META, request, request.upload_handlers)
            post_data, files = parser.parse()
        else:
            post_data = request.POST
            files = request.FILES
        
        print(f"[admin_product_update] post_data keys: {list(post_data.keys())}")
        print(f"[admin_product_update] post_data: {dict(post_data)}")
        
        # Handle multipart form data (with or without file uploads)
        title = post_data.get("title")
        description = post_data.get("description")
        price = post_data.get("price")
        stock = post_data.get("stock")
        category = post_data.get("category")
        is_trending = post_data.get("is_trending")
        
        print(f"[admin_product_update] Received: title={title}, price={price}, stock={stock}, category={category}")
        
        if title:
            product.title = sanitize_string(title, max_length=255)
        if description is not None:
            product.description = sanitize_string(description, max_length=5000)
        if price:
            try:
                product.price = float(price)
            except (ValueError, TypeError):
                pass
        if stock is not None and stock != '':
            try:
                product.stock = int(stock)
            except (ValueError, TypeError):
                pass
        if category:
            product.category = sanitize_string(category, max_length=100)
        
        # Handle is_trending - always update based on what's sent
        # Checkbox sends "true" when checked, FormData doesn't include it when unchecked
        product.is_trending = post_data.get("is_trending") == "true"
        
        # Handle expiry and manufacturing dates
        from datetime import datetime
        expiry_str = post_data.get("expiry_date", "")
        mfg_str = post_data.get("manufacturing_date", "")
        if expiry_str:
            try:
                product.expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        elif expiry_str == '':
            product.expiry_date = None
        if mfg_str:
            try:
                product.manufacturing_date = datetime.strptime(mfg_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        elif mfg_str == '':
            product.manufacturing_date = None
        
        # Handle ingredients, benefits, and how_to_use - always update
        ingredients = post_data.get("ingredients", "")
        product.ingredients = [i.strip() for i in ingredients.split('\n') if i.strip()] if ingredients else []
        
        benefits = post_data.get("benefits", "")
        product.benefits = [b.strip() for b in benefits.split('\n') if b.strip()] if benefits else []
        
        how_to_use = post_data.get("how_to_use", "")
        product.how_to_use = [h.strip() for h in how_to_use.split('\n') if h.strip()] if how_to_use else []
        
        # Handle new image uploads
        uploaded_files = files.getlist('images') if hasattr(files, 'getlist') else []
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
        print(f"[admin_product_update] Product {product.id} saved successfully. New values: title={product.title}, price={product.price}, stock={product.stock}")
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
        if 'is_trending' in body:
            product.is_trending = body['is_trending']
        if 'images' in body:
            product.images = body['images']
        if 'ingredients' in body:
            product.ingredients = [i.strip() for i in body['ingredients'] if isinstance(i, str) and i.strip()]
        if 'benefits' in body:
            product.benefits = [b.strip() for b in body['benefits'] if isinstance(b, str) and b.strip()]
        if 'how_to_use' in body:
            product.how_to_use = [h.strip() for h in body['how_to_use'] if isinstance(h, str) and h.strip()]

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
        banners = Banner.objects.all().order_by('order', '-created_at')
        return JsonResponse([b.to_dict() for b in banners], safe=False)

    # Create (supports multipart/form-data with `image` file)
    if request.method == 'POST':
        # try to read multipart fields first
        title = None
        banner_type = 'featured'
        description = ''
        link_url = ''
        is_active = True
        order = 0
        
        if request.content_type and request.content_type.startswith('multipart/'):
            title = request.POST.get('title')
            banner_type = request.POST.get('banner_type', 'featured')
            description = request.POST.get('description', '')
            link_url = request.POST.get('link_url', '')
            is_active = request.POST.get('is_active', 'true').lower() in ('1', 'true', 'yes')
            try:
                order = int(request.POST.get('order', 0))
            except Exception:
                order = 0
            image = request.FILES.get('image')
        else:
            try:
                body = json.loads(request.body)
            except Exception:
                return HttpResponseBadRequest()
            title = body.get('title')
            banner_type = body.get('banner_type', 'featured')
            description = body.get('description', '')
            link_url = body.get('link_url', '')
            is_active = bool(body.get('is_active', True))
            order = int(body.get('order', 0))
            image = None

        if not title:
            return JsonResponse({"error": "title is required"}, status=400)

        banner = Banner.objects.create(
            title=title,
            banner_type=banner_type,
            description=description,
            link_url=link_url,
            is_active=is_active,
            order=order
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

        return JsonResponse({"message": "Banner created", "banner": banner.to_dict()}, status=201)

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
        if 'banner_type' in body:
            banner.banner_type = body.get('banner_type')
        if 'description' in body:
            banner.description = body.get('description')
        if 'link_url' in body:
            banner.link_url = body.get('link_url')
        if 'is_active' in body:
            banner.is_active = bool(body.get('is_active'))
        if 'order' in body:
            try:
                banner.order = int(body.get('order', banner.order))
            except Exception:
                pass

        banner.save()
        return JsonResponse({"message": "Banner updated", "banner": banner.to_dict()})

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


# ============================================================================
# SOCIAL FEATURES - Follow/Unfollow System
# ============================================================================

@csrf_exempt
def follow_user(request, user_id):
    """Follow a user - creates follow relationship and notification."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
        if current_user.is_staff and current_user.is_superuser:
            return JsonResponse({"error": "Admin users cannot follow other users."}, status=403)
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get user to follow
    try:
        user_to_follow = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Prevent self-follow
    if current_user.id == user_to_follow.id:
        return JsonResponse({"error": "You cannot follow yourself"}, status=400)
    
    # Check if already following
    if UserFollow.objects.filter(follower=current_user, following=user_to_follow).exists():
        return JsonResponse({"error": "Already following this user"}, status=400)
    
    # Create follow relationship
    UserFollow.objects.create(follower=current_user, following=user_to_follow)
    
    # Create notification
    Notification.objects.create(
        user=user_to_follow,
        actor=current_user,
        notification_type='follow',
        message=f'{current_user.name} started following you'
    )
    
    # Invalidate recommendation cache (social connections affect recommendations)
    from .recommender import invalidate_user_recommendation_cache
    invalidate_user_recommendation_cache(current_user.id)
    
    return JsonResponse({
        "message": f"You are now following {user_to_follow.name}",
        "followers_count": user_to_follow.get_followers_count(),
        "following_count": current_user.get_following_count()
    })


@csrf_exempt
def unfollow_user(request, user_id):
    """Unfollow a user - removes follow relationship."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
        if current_user.is_staff and current_user.is_superuser:
            return JsonResponse({"error": "Admin users cannot unfollow other users."}, status=403)
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get user to unfollow
    try:
        user_to_unfollow = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Check if following exists
    try:
        follow = UserFollow.objects.get(follower=current_user, following=user_to_unfollow)
        follow.delete()
    except UserFollow.DoesNotExist:
        return JsonResponse({"error": "You are not following this user"}, status=400)
    
    # Invalidate recommendation cache (social connections affect recommendations)
    from .recommender import invalidate_user_recommendation_cache
    invalidate_user_recommendation_cache(current_user.id)
    
    return JsonResponse({
        "message": f"You unfollowed {user_to_unfollow.name}",
        "followers_count": user_to_unfollow.get_followers_count(),
        "following_count": current_user.get_following_count()
    })


@csrf_exempt
def get_followers(request, user_id):
    """Get list of users following the specified user."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user (optional for public profiles)
    current_user = None
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        try:
            payload = decode_jwt(token)
            current_user = AppUser.objects.get(pk=payload['user_id'])
        except Exception:
            pass
    
    # Get target user
    try:
        target_user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Get followers with pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size
    
    followers = UserFollow.objects.filter(following=target_user).select_related('follower')[offset:offset + page_size]
    total_count = UserFollow.objects.filter(following=target_user).count()
    
    followers_data = []
    for follow in followers:
        follower = follow.follower
        follower_data = follower.to_profile_dict(requesting_user=current_user)
        followers_data.append(follower_data)
    
    return JsonResponse({
        "followers": followers_data,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "has_more": total_count > offset + page_size
    })


@csrf_exempt
def get_following(request, user_id):
    """Get list of users that the specified user follows."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user (optional for public profiles)
    current_user = None
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        try:
            payload = decode_jwt(token)
            current_user = AppUser.objects.get(pk=payload['user_id'])
        except Exception:
            pass
    
    # Get target user
    try:
        target_user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Get following with pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size
    
    following = UserFollow.objects.filter(follower=target_user).select_related('following')[offset:offset + page_size]
    total_count = UserFollow.objects.filter(follower=target_user).count()
    
    following_data = []
    for follow in following:
        followed_user = follow.following
        followed_data = followed_user.to_profile_dict(requesting_user=current_user)
        following_data.append(followed_data)
    
    return JsonResponse({
        "following": following_data,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "has_more": total_count > offset + page_size
    })


@csrf_exempt
def get_user_profile_social(request, user_id):
    """Get detailed user profile with social stats."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user (optional)
    current_user = None
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        try:
            payload = decode_jwt(token)
            current_user = AppUser.objects.get(pk=payload['user_id'])
        except Exception:
            pass
    
    # Get target user
    try:
        target_user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Get profile with social stats
    profile = target_user.to_profile_dict(requesting_user=current_user)
    
    # Add liked products count
    profile['liked_products_count'] = target_user.liked_products.count()
    
    return JsonResponse(profile)


@csrf_exempt
def search_users(request):
    """Search for users by name or email."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user (optional)
    current_user = None
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        try:
            payload = decode_jwt(token)
            current_user = AppUser.objects.get(pk=payload['user_id'])
        except Exception:
            pass
    
    # Get search query
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({"error": "Search query must be at least 2 characters"}, status=400)
    
    # Search users
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size
    
    users = AppUser.objects.filter(
        models.Q(name__icontains=query) | models.Q(email__icontains=query)
    )[offset:offset + page_size]
    
    total_count = AppUser.objects.filter(
        models.Q(name__icontains=query) | models.Q(email__icontains=query)
    ).count()
    
    users_data = []
    for user in users:
        # Exclude current user from results
        if current_user and user.id == current_user.id:
            continue
        user_data = user.to_profile_dict(requesting_user=current_user)
        users_data.append(user_data)
    
    return JsonResponse({
        "users": users_data,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "has_more": total_count > offset + page_size
    })


@csrf_exempt
def get_suggested_users(request):
    """Get suggested users to follow."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get users that current user is NOT following
    following_ids = UserFollow.objects.filter(follower=current_user).values_list('following_id', flat=True)
    
    # Get users with most followers (excluding already followed, self, and admin users)
    suggested_users = AppUser.objects.exclude(
        id__in=list(following_ids) + [current_user.id]
    ).filter(
        is_staff=False,
        is_superuser=False
    ).annotate(
        followers_count=models.Count('followers')
    ).order_by('-followers_count')[:20]
    
    users_data = []
    for user in suggested_users:
        user_data = user.to_profile_dict(requesting_user=current_user)
        users_data.append(user_data)
    
    return JsonResponse({"suggested_users": users_data})


@csrf_exempt
def get_mutual_followers(request, user_id):
    """Get mutual followers between current user and specified user."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get target user
    try:
        target_user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Get mutual followers (users following both current_user and target_user)
    current_follower_ids = UserFollow.objects.filter(following=current_user).values_list('follower_id', flat=True)
    target_follower_ids = UserFollow.objects.filter(following=target_user).values_list('follower_id', flat=True)
    
    mutual_ids = set(current_follower_ids).intersection(set(target_follower_ids))
    
    mutual_users = AppUser.objects.filter(id__in=mutual_ids)
    
    users_data = []
    for user in mutual_users:
        user_data = user.to_profile_dict(requesting_user=current_user)
        users_data.append(user_data)
    
    return JsonResponse({
        "mutual_followers": users_data,
        "count": len(users_data)
    })


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@csrf_exempt
def get_notifications(request):
    """Get user's notifications including unread messages."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    from django.db.models import Q
    from api.models import Conversation, Message
    
    # Filter by read status if specified
    is_read = request.GET.get('is_read')
    notifications_query = Notification.objects.filter(user=current_user)
    
    if is_read is not None:
        is_read_bool = is_read.lower() == 'true'
        notifications_query = notifications_query.filter(is_read=is_read_bool)
    
    # Get regular notifications
    notifications_data = [notif.to_dict() for notif in notifications_query.select_related('actor')]
    
    # Get unread messages as notifications
    conversations = Conversation.objects.filter(
        Q(user1=current_user) | Q(user2=current_user)
    )
    
    # Build message notification filter
    message_filter = Q(conversation__in=conversations) & ~Q(sender=current_user)
    if is_read is not None:
        is_read_bool = is_read.lower() == 'true'
        message_filter &= Q(is_read=is_read_bool)
    else:
        # By default, only show unread messages as notifications
        message_filter &= Q(is_read=False)
    
    unread_messages = Message.objects.filter(message_filter).select_related('sender', 'conversation').order_by('-created_at')
    
    # Convert unread messages to notification format
    for msg in unread_messages:
        msg_content = msg.content[:50] + '...' if len(msg.content) > 50 else msg.content
        notifications_data.append({
            'id': f'msg_{msg.id}',
            'actor': {
                'id': msg.sender.id,
                'name': msg.sender.name,
                'email': msg.sender.email,
                'bio': msg.sender.bio or '',
            },
            'notification_type': 'message',
            'message': f'sent you a message: "{msg_content}"',
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat(),
            'conversation_id': msg.conversation.id,
        })
    
    # Sort all notifications by created_at descending
    notifications_data.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size
    total_count = len(notifications_data)
    
    paginated_notifications = notifications_data[offset:offset + page_size]
    
    return JsonResponse({
        "notifications": paginated_notifications,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "has_more": total_count > offset + page_size
    })


@csrf_exempt
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get notification
    try:
        notification = Notification.objects.get(pk=notification_id, user=current_user)
        notification.is_read = True
        notification.save()
        
        unread_count = Notification.objects.filter(user=current_user, is_read=False).count()
        
        return JsonResponse({
            "message": "Notification marked as read",
            "unread_count": unread_count
        })
    except Notification.DoesNotExist:
        return JsonResponse({"error": "Notification not found"}, status=404)


@csrf_exempt
def mark_all_notifications_read(request):
    """Mark all user's notifications as read."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Mark all as read
    updated_count = Notification.objects.filter(user=current_user, is_read=False).update(is_read=True)
    
    return JsonResponse({
        "message": f"{updated_count} notifications marked as read",
        "unread_count": 0
    })


@csrf_exempt
def get_unread_notifications_count(request):
    """Get count of unread notifications including unread messages."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    from django.db.models import Q
    from api.models import Conversation, Message
    
    # Count regular unread notifications
    notification_count = Notification.objects.filter(user=current_user, is_read=False).count()
    
    # Count unread messages
    conversations = Conversation.objects.filter(
        Q(user1=current_user) | Q(user2=current_user)
    )
    message_count = Message.objects.filter(
        conversation__in=conversations,
        is_read=False
    ).exclude(sender=current_user).count()
    
    unread_count = notification_count + message_count
    
    return JsonResponse({"unread_count": unread_count})


def get_time_ago(dt):
    """Helper function to get human-readable time ago."""
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days}d ago"
    else:
        weeks = diff.days // 7
        return f"{weeks}w ago"


@csrf_exempt
def get_friends_product_activities(request):
    """Get friends' activities on products (likes)."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    # Get authenticated user
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception as e:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get all users that current user follows (friends)
    following_ids = list(UserFollow.objects.filter(follower=current_user).values_list('following_id', flat=True))
    
    if not following_ids:
        return JsonResponse({"activities": [], "activities_by_product": {}})
    
    # Get product IDs from query param (optional - to filter activities for specific products)
    product_ids_param = request.GET.get('product_ids')
    product_ids = None
    if product_ids_param:
        try:
            product_ids = [int(pid) for pid in product_ids_param.split(',')]
        except ValueError:
            pass
    
    activities = []
    
    # Get friends' liked products
    liked_query = UserLikedProduct.objects.filter(
        user_id__in=following_ids
    ).select_related('user', 'product')
    
    if product_ids:
        liked_query = liked_query.filter(product_id__in=product_ids)
    
    # Limit to recent activities (last 30 days)
    from datetime import timedelta
    from django.utils import timezone
    thirty_days_ago = timezone.now() - timedelta(days=30)
    liked_query = liked_query.filter(created_at__gte=thirty_days_ago).order_by('-created_at')[:50]
    
    for like in liked_query:
        activities.append({
            'type': 'liked',
            'user': {
                'id': like.user.id,
                'name': like.user.name
            },
            'product_id': like.product.id,
            'product_title': like.product.title,
            'created_at': like.created_at.isoformat(),
            'time_ago': get_time_ago(like.created_at)
        })
    
    # Group by product_id for easy lookup
    activities_by_product = {}
    for activity in activities:
        pid = activity['product_id']
        if pid not in activities_by_product:
            activities_by_product[pid] = []
        activities_by_product[pid].append(activity)
    
    return JsonResponse({
        "activities": activities,
        "activities_by_product": activities_by_product
    })


# ============================================================================
# CHAT / MESSAGING ENDPOINTS
# ============================================================================

@csrf_exempt
def get_conversations(request):
    """Get all conversations for the current user."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get all conversations where user is either user1 or user2
    from django.db.models import Q
    from api.models import Conversation
    
    conversations = Conversation.objects.filter(
        Q(user1=current_user) | Q(user2=current_user)
    ).select_related('user1', 'user2')
    
    conversations_data = [conv.to_dict(current_user.id) for conv in conversations]
    
    return JsonResponse({"conversations": conversations_data})


@csrf_exempt
def get_or_create_conversation(request, other_user_id):
    """Get or create a conversation with another user."""
    if request.method not in ['GET', 'POST']:
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get the other user
    try:
        other_user = AppUser.objects.get(pk=other_user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Check if both users follow each other
    from api.models import UserFollow, Conversation
    
    user_follows_other = UserFollow.objects.filter(
        follower=current_user, following=other_user
    ).exists()
    other_follows_user = UserFollow.objects.filter(
        follower=other_user, following=current_user
    ).exists()
    
    if not (user_follows_other and other_follows_user):
        return JsonResponse({
            "error": "You can only chat with users who follow you back"
        }, status=403)
    
    # Get or create conversation (ensure user1_id < user2_id for consistency)
    user1_id = min(current_user.id, other_user.id)
    user2_id = max(current_user.id, other_user.id)
    
    user1 = AppUser.objects.get(pk=user1_id)
    user2 = AppUser.objects.get(pk=user2_id)
    
    conversation, created = Conversation.objects.get_or_create(
        user1=user1,
        user2=user2
    )
    
    return JsonResponse({
        "conversation": conversation.to_dict(current_user.id),
        "created": created
    })


@csrf_exempt
def get_messages(request, conversation_id):
    """Get all messages in a conversation."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    from api.models import Conversation, Message
    
    # Get conversation and verify user is part of it
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({"error": "Conversation not found"}, status=404)
    
    if conversation.user1.id != current_user.id and conversation.user2.id != current_user.id:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Get messages with pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 50))
    offset = (page - 1) * page_size
    
    messages = Message.objects.filter(
        conversation=conversation
    ).select_related('sender').order_by('created_at')[offset:offset + page_size]
    
    total_count = Message.objects.filter(conversation=conversation).count()
    
    messages_data = [msg.to_dict() for msg in messages]
    
    # Mark messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=current_user).update(is_read=True)
    
    return JsonResponse({
        "messages": messages_data,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "has_more": total_count > offset + page_size
    })


@csrf_exempt
def send_message(request, conversation_id):
    """Send a message in a conversation."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    from api.models import Conversation, Message
    
    # Get conversation and verify user is part of it
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({"error": "Conversation not found"}, status=404)
    
    if conversation.user1.id != current_user.id and conversation.user2.id != current_user.id:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Get message content
    body = json.loads(request.body)
    content = body.get('content', '').strip()
    
    if not content:
        return JsonResponse({"error": "Message content is required"}, status=400)
    
    # Create message
    message = Message.objects.create(
        conversation=conversation,
        sender=current_user,
        content=content
    )
    
    # Update conversation timestamp
    conversation.save()
    
    return JsonResponse({
        "message": message.to_dict(),
        "success": True
    })


@csrf_exempt
def edit_message(request, message_id):
    """Edit a message."""
    if request.method != 'PUT':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    from api.models import Message
    
    # Get message
    try:
        message = Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)
    
    # Verify user is the sender
    if message.sender.id != current_user.id:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Get new content
    body = json.loads(request.body)
    new_content = body.get('content', '').strip()
    
    if not new_content:
        return JsonResponse({"error": "Message content is required"}, status=400)
    
    # Update message
    message.content = new_content
    message.save()
    
    return JsonResponse({
        "message": message.to_dict(),
        "success": True
    })


@csrf_exempt
def delete_message(request, message_id):
    """Delete a message."""
    if request.method != 'DELETE':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    from api.models import Message
    
    # Get message
    try:
        message = Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)
    
    # Verify user is the sender
    if message.sender.id != current_user.id:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Delete message
    message.delete()
    
    return JsonResponse({
        "success": True,
        "message": "Message deleted successfully"
    })


@csrf_exempt
def get_unread_messages_count(request):
    """Get count of unread messages."""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    from django.db.models import Q
    from api.models import Conversation, Message
    
    # Get all conversations for this user
    conversations = Conversation.objects.filter(
        Q(user1=current_user) | Q(user2=current_user)
    )
    
    # Count unread messages across all conversations
    unread_count = Message.objects.filter(
        conversation__in=conversations,
        is_read=False
    ).exclude(sender=current_user).count()
    
    return JsonResponse({"unread_count": unread_count})


@csrf_exempt
def share_product(request):
    """Share a product with another user."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Check if user can share products (not admin)
    if current_user.is_staff and current_user.is_superuser:
        return JsonResponse({"error": "Admins cannot share products"}, status=403)
    
    from django.db.models import Q
    from api.models import Conversation, Message, UserFollow, ProductShare
    
    # Get request data
    body = json.loads(request.body)
    product_id = body.get('product_id')
    recipient_id = body.get('recipient_id')
    message_text = body.get('message', '').strip()
    
    print(f"DEBUG share_product: user={current_user.id}, product={product_id}, recipient={recipient_id}")
    
    if not product_id or not recipient_id:
        return JsonResponse({"error": "Product ID and recipient ID are required"}, status=400)
    
    # Get product
    try:
        product = Product.objects.get(pk=product_id)
        print(f"DEBUG: Product found: {product.title}")
    except Product.DoesNotExist:
        print(f"DEBUG: Product not found: {product_id}")
        return JsonResponse({"error": "Product not found"}, status=404)
    
    # Get recipient
    try:
        recipient = AppUser.objects.get(pk=recipient_id)
        print(f"DEBUG: Recipient found: {recipient.name} ({recipient.email})")
    except AppUser.DoesNotExist:
        print(f"DEBUG: Recipient not found: {recipient_id}")
        return JsonResponse({"error": "Recipient not found"}, status=404)
    
    # Verify mutual following
    following = UserFollow.objects.filter(follower=current_user, following=recipient).exists()
    followed = UserFollow.objects.filter(follower=recipient, following=current_user).exists()
    
    print(f"DEBUG: I follow them: {following}, They follow me: {followed}")
    
    if not (following and followed):
        return JsonResponse({"error": "Can only share with mutual followers"}, status=403)
    
    # Create or get conversation
    conversation = Conversation.objects.filter(
        Q(user1=current_user, user2=recipient) |
        Q(user1=recipient, user2=current_user)
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create(
            user1=current_user,
            user2=recipient
        )
    
    # Create product share message
    share_message = Message.objects.create(
        conversation=conversation,
        sender=current_user,
        content=message_text or f"Check out this product: {product.title}",
        message_type='product',
        shared_product=product
    )
    
    # Create product share record
    product_share = ProductShare.objects.create(
        product=product,
        sender=current_user,
        recipient=recipient,
        message=message_text
    )
    
    # Update conversation timestamp
    conversation.save()
    
    return JsonResponse({
        "success": True,
        "message": share_message.to_dict(),
        "share": product_share.to_dict()
    })


@csrf_exempt
def check_product_allergies(request, product_id):
    """Check if a product contains any allergens for the current user."""
    if request.method != "GET":
        return HttpResponseBadRequest()
    
    # Get current user
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    payload = decode_jwt(token)
    if not payload:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        user = AppUser.objects.get(pk=payload["user_id"])
        product = Product.objects.get(pk=product_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    
    # Check for allergen matches
    user_allergies = [allergy.lower().strip() for allergy in user.allergies]
    product_ingredients = [ing.lower().strip() for ing in product.ingredients]
    
    allergens_found = []
    for allergy in user_allergies:
        for ingredient in product_ingredients:
            if allergy in ingredient or ingredient in allergy:
                allergens_found.append(ingredient)
    
    has_allergens = len(allergens_found) > 0
    
    # Find alternative products if allergens found
    alternative_products = []
    if has_allergens:
        # Find products in same category without the allergens
        all_products = Product.objects.filter(category=product.category).exclude(pk=product_id)
        
        for alt_product in all_products:
            alt_ingredients = [ing.lower().strip() for ing in alt_product.ingredients]
            has_user_allergen = False
            
            for allergy in user_allergies:
                for ing in alt_ingredients:
                    if allergy in ing or ing in allergy:
                        has_user_allergen = True
                        break
                if has_user_allergen:
                    break
            
            if not has_user_allergen:
                alternative_products.append(alt_product.to_dict())
                if len(alternative_products) >= 3:  # Limit to 3 alternatives
                    break
    
    return JsonResponse({
        "has_allergens": has_allergens,
        "allergens_found": allergens_found,
        "product": product.to_dict(),
        "alternatives": alternative_products
    })


@csrf_exempt
def update_user_allergies(request):
    """Update user's allergy information."""
    if request.method != "PUT":
        return HttpResponseBadRequest()
    
    # Get current user
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JsonResponse({"error": "Authentication required"}, status=401)


@csrf_exempt
def check_cart_allergies(request):
    """Check if cart items contain any allergens for the current user."""
    if request.method != "POST":
        return HttpResponseBadRequest()
    
    # Get current user
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    payload = decode_jwt(token)
    if not payload:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        user = AppUser.objects.get(pk=payload["user_id"])
        data = json.loads(request.body)
        product_ids = data.get("product_ids", [])
        
        if not product_ids:
            return JsonResponse({"error": "No products provided"}, status=400)
        
        # Get user allergies
        user_allergies = [allergy.lower().strip() for allergy in user.allergies]
        
        if not user_allergies:
            return JsonResponse({
                "has_allergens": False,
                "products_with_allergens": []
            })
        
        # Check each product for allergens
        products_with_allergens = []
        
        for product_id in product_ids:
            try:
                product = Product.objects.get(pk=product_id)
                product_ingredients = [ing.lower().strip() for ing in product.ingredients]
                
                allergens_found = []
                for allergy in user_allergies:
                    for ingredient in product_ingredients:
                        if allergy in ingredient or ingredient in allergy:
                            if ingredient not in allergens_found:
                                allergens_found.append(ingredient)
                
                if allergens_found:
                    # Find alternative products
                    alternative_products = []
                    all_products = Product.objects.filter(category=product.category).exclude(pk=product_id)
                    
                    for alt_product in all_products:
                        alt_ingredients = [ing.lower().strip() for ing in alt_product.ingredients]
                        has_user_allergen = False
                        
                        for allergy in user_allergies:
                            for ing in alt_ingredients:
                                if allergy in ing or ing in allergy:
                                    has_user_allergen = True
                                    break
                            if has_user_allergen:
                                break
                        
                        if not has_user_allergen:
                            alternative_products.append(alt_product.to_dict())
                            if len(alternative_products) >= 3:
                                break
                    
                    products_with_allergens.append({
                        "product": product.to_dict(),
                        "allergens_found": allergens_found,
                        "alternatives": alternative_products
                    })
            
            except Product.DoesNotExist:
                continue
        
        return JsonResponse({
            "has_allergens": len(products_with_allergens) > 0,
            "products_with_allergens": products_with_allergens
        })
        
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@csrf_exempt
def update_user_allergies(request):
    """Update user's allergy information."""
    if request.method != "PUT":
        return HttpResponseBadRequest()
    
    # Get current user
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    payload = decode_jwt(token)
    if not payload:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        user = AppUser.objects.get(pk=payload["user_id"])
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    body = json.loads(request.body)
    allergies = body.get("allergies", [])
    
    # Validate and sanitize allergies
    if not isinstance(allergies, list):
        return JsonResponse({"error": "Allergies must be a list"}, status=400)
    
    sanitized_allergies = [sanitize_string(allergy, max_length=100) for allergy in allergies if allergy]
    
    user.allergies = sanitized_allergies
    user.save()
    
    return JsonResponse({
        "success": True,
        "user": user.to_dict()
    })


def get_banners(request):
    """Get active banners, optionally filtered by type"""
    banner_type = request.GET.get('type', None)
    
    banners = Banner.objects.filter(is_active=True)
    
    if banner_type:
        banners = banners.filter(banner_type=banner_type)
    
    return JsonResponse({
        "banners": [banner.to_dict() for banner in banners]
    })


# ============================================================================
# WALLET ENDPOINTS
# ============================================================================

@csrf_exempt
def get_wallet_balance(request):
    """Get user's wallet balance"""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get or create wallet
    wallet, created = Wallet.objects.get_or_create(user=current_user)
    
    return JsonResponse({
        "wallet": wallet.to_dict()
    })


@csrf_exempt
def add_money_to_wallet(request):
    """Add money to wallet"""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        from decimal import Decimal
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        
        if amount <= 0:
            return JsonResponse({"error": "Amount must be greater than 0"}, status=400)
        
        # Get or create wallet
        wallet, created = Wallet.objects.get_or_create(user=current_user)
        
        # Add money to wallet
        wallet.balance += amount
        wallet.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='credit',
            amount=amount,
            status='completed',
            description=f"Added ${amount} to wallet"
        )
        
        return JsonResponse({
            "success": True,
            "wallet": wallet.to_dict(),
            "message": f"${amount} added to your wallet successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def get_wallet_transactions(request):
    """Get wallet transaction history"""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    # Get or create wallet
    wallet, created = Wallet.objects.get_or_create(user=current_user)
    
    # Get transactions
    transactions = WalletTransaction.objects.filter(wallet=wallet)
    
    return JsonResponse({
        "transactions": [t.to_dict() for t in transactions],
        "wallet_balance": float(wallet.balance)
    })


@csrf_exempt
def create_order_with_wallet(request):
    """Create order and pay using wallet"""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        current_user = AppUser.objects.get(pk=payload['user_id'])
    except Exception:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        from decimal import Decimal
        data = json.loads(request.body)
        order_total = Decimal(str(data.get('total', 0)))
        use_wallet = data.get('use_wallet', False)
        
        if order_total <= 0:
            return JsonResponse({"error": "Invalid order total"}, status=400)
        
        # Get or create wallet
        wallet, created = Wallet.objects.get_or_create(user=current_user)
        
        # Check if using wallet and has sufficient balance
        if use_wallet:
            if wallet.balance < order_total:
                return JsonResponse({
                    "error": "Insufficient wallet balance",
                    "wallet_balance": float(wallet.balance),
                    "required": order_total
                }, status=400)
            
            # Deduct from wallet
            wallet.balance -= order_total
            wallet.save()
            
            # Create order
            order = Order.objects.create(
                user=current_user,
                total=order_total,
                status='confirmed'
            )
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='debit',
                amount=order_total,
                status='completed',
                description=f"Payment for Order #{order.id}",
                order=order
            )
            
            # Clear cart
            try:
                cart = Cart.objects.get(user=current_user)
                cart_items = CartItem.objects.filter(cart=cart)
                
                # Create order items
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        qty=item.qty,
                        price=item.product.price
                    )
                
                # Clear cart
                cart_items.delete()
            except Cart.DoesNotExist:
                pass
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "wallet_balance": float(wallet.balance),
                "message": "Order placed successfully using wallet"
            })
        else:
            # Regular order creation (non-wallet payment)
            order = Order.objects.create(
                user=current_user,
                total=order_total,
                status='created'
            )
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "message": "Order created successfully"
            })
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ==================== QUICK BUY (BOOK NOW) ENDPOINT ====================

@csrf_exempt
def quick_buy(request):
    """Quick buy - create order directly from product (Book Now button)"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        user_id = payload.get('user_id')
        current_user = AppUser.objects.get(pk=user_id)
    except:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        qty = data.get('qty', 1)
        
        if not product_id:
            return JsonResponse({"error": "Product ID is required"}, status=400)
        
        # Get product
        product = Product.objects.get(pk=product_id)
        
        if product.stock < qty:
            return JsonResponse({"error": "Insufficient stock"}, status=400)
        
        # Calculate total
        order_total = product.price * qty
        
        # Create order directly (without cart)
        order = Order.objects.create(
            user=current_user,
            total=order_total,
            status='pending',
            payment_status='pending'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            qty=qty,
            price=product.price
        )
        
        return JsonResponse({
            "success": True,
            "order_id": order.id,
            "order_number": order.order_number,
            "total": float(order_total),
            "message": "Order created successfully"
        })
        
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ==================== CASHFREE PAYMENT ENDPOINTS ====================

@csrf_exempt
def create_payment_order(request):
    """Create order and initialize Cashfree payment"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        user_id = payload.get('user_id')
        current_user = AppUser.objects.get(pk=user_id)
    except:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        data = json.loads(request.body)
        payment_method = data.get('payment_method', 'cashfree')
        shipping_address_id = data.get('shipping_address_id')
        billing_address_id = data.get('billing_address_id')
        
        # Get cart items
        cart = Cart.objects.get(user=current_user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            return JsonResponse({"error": "Cart is empty"}, status=400)
        
        # Calculate total
        order_total = sum(item.product.price * item.qty for item in cart_items)
        
        # Get addresses
        shipping_address = None
        billing_address = None
        if shipping_address_id:
            shipping_address = Address.objects.get(id=shipping_address_id, user=current_user)
        if billing_address_id:
            billing_address = Address.objects.get(id=billing_address_id, user=current_user)
        
        # Create order
        order = Order.objects.create(
            user=current_user,
            total=order_total,
            status='pending',
            payment_status='pending',
            shipping_address=shipping_address,
            billing_address=billing_address
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                qty=item.qty,
                price=item.product.price
            )
        
        # Handle payment method
        if payment_method == 'cod':
            # Cash on Delivery
            order.payment_status = 'cod'
            order.status = 'confirmed'
            order.save()
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_method": "cod",
                "message": "Order placed successfully with Cash on Delivery"
            })
        
        elif payment_method == 'wallet':
            # Wallet payment
            wallet = Wallet.objects.get(user=current_user)
            
            if wallet.balance < order_total:
                order.delete()
                return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            
            # Deduct from wallet
            wallet.balance -= order_total
            wallet.save()
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='debit',
                amount=order_total,
                status='completed',
                description=f'Payment for order {order.order_number}',
                order=order
            )
            
            order.payment_status = 'success'
            order.status = 'confirmed'
            order.save()
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_method": "wallet",
                "wallet_balance": float(wallet.balance),
                "message": "Order placed successfully using wallet"
            })
        
        else:
            # Cashfree payment
            from .cashfree_utils import cashfree
            
            # Prepare customer details
            customer_details = {
                'customer_id': str(current_user.id),
                'customer_name': current_user.name,
                'customer_email': current_user.email,
                'customer_phone': shipping_address.phone if shipping_address else '9999999999'
            }
            
            # Get return URL from request or use default
            return_url = data.get('return_url', 'http://localhost:3000/payment/success')
            
            # Create Cashfree order
            cf_response = cashfree.create_order(
                order_id=order.order_number,
                amount=order_total,
                customer_details=customer_details,
                return_url=return_url
            )
            
            if not cf_response.get('success'):
                order.delete()
                return JsonResponse({
                    "error": "Failed to initialize payment",
                    "message": cf_response.get('message')
                }, status=400)
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                cashfree_order_id=cf_response.get('order_id'),
                payment_method='cashfree',
                amount=order_total,
                status='initiated',
                payment_session_id=cf_response.get('payment_session_id'),
                transaction_data=cf_response.get('data', {})
            )
            
            order.payment_status = 'initiated'
            order.save()
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_session_id": payment.payment_session_id,
                "cashfree_order_id": payment.cashfree_order_id,
                "amount": float(order_total),
                "message": "Payment initialized successfully"
            })
            
    except Cart.DoesNotExist:
        return JsonResponse({"error": "Cart not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def retry_payment_order(request):
    """Retry payment for an existing order"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        user_id = payload.get('user_id')
        current_user = AppUser.objects.get(pk=user_id)
    except:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        payment_method = data.get('payment_method', 'cashfree')
        return_url = data.get('return_url', '')
        
        # Get the existing order
        order = Order.objects.get(id=order_id, user=current_user)
        
        # Check if order is already paid
        if order.payment_status == 'success':
            return JsonResponse({"error": "Order already paid"}, status=400)
        
        # Get order total
        order_total = order.total
        
        # Handle payment method
        if payment_method == 'cod':
            # Cash on Delivery
            order.payment_status = 'cod'
            order.status = 'confirmed'
            order.save()
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_method": "cod",
                "message": "Order confirmed with Cash on Delivery"
            })
        
        elif payment_method == 'wallet':
            # Wallet payment
            wallet = Wallet.objects.get(user=current_user)
            
            if wallet.balance < order_total:
                return JsonResponse({"error": "Insufficient wallet balance"}, status=400)
            
            # Deduct from wallet
            wallet.balance -= order_total
            wallet.save()
            
            # Create or update payment record
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'payment_method': 'wallet',
                    'amount': order_total,
                    'status': 'success'
                }
            )
            
            if not created:
                payment.payment_method = 'wallet'
                payment.status = 'success'
                payment.amount = order_total
                payment.save()
            
            order.payment_status = 'success'
            order.status = 'confirmed'
            order.save()
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_method": "wallet",
                "message": "Payment successful via wallet"
            })
        
        elif payment_method == 'cashfree':
            # Cashfree payment
            from .cashfree_utils import CashfreePayment
            
            cf = CashfreePayment()
            cf_response = cf.create_order(
                order_id=order.order_number,
                order_amount=float(order_total),
                customer_details={
                    "customer_id": str(current_user.id),
                    "customer_email": current_user.email,
                    "customer_phone": getattr(order.shipping_address, 'phone', '9999999999')
                },
                order_meta={
                    "return_url": return_url,
                    "notify_url": f"{request.scheme}://{request.get_host()}/api/payment/webhook/"
                }
            )
            
            if not cf_response.get('success'):
                return JsonResponse({
                    "error": "Failed to initialize payment",
                    "message": cf_response.get('message')
                }, status=400)
            
            # Create or update payment record
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'cashfree_order_id': cf_response.get('order_id'),
                    'payment_method': 'cashfree',
                    'amount': order_total,
                    'status': 'initiated',
                    'payment_session_id': cf_response.get('payment_session_id'),
                    'transaction_data': cf_response.get('data', {})
                }
            )
            
            if not created:
                payment.cashfree_order_id = cf_response.get('order_id')
                payment.payment_method = 'cashfree'
                payment.status = 'initiated'
                payment.payment_session_id = cf_response.get('payment_session_id')
                payment.transaction_data = cf_response.get('data', {})
                payment.save()
            
            order.payment_status = 'initiated'
            order.save()
            
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_session_id": payment.payment_session_id,
                "cashfree_order_id": payment.cashfree_order_id,
                "amount": float(order_total),
                "message": "Payment initialized successfully"
            })
            
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    except Wallet.DoesNotExist:
        return JsonResponse({"error": "Wallet not found. Please contact support."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def verify_payment(request):
    """Verify Cashfree payment and update order status"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        user_id = payload.get('user_id')
        current_user = AppUser.objects.get(pk=user_id)
    except:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        data = json.loads(request.body)
        order_number = data.get('order_number')
        
        if not order_number:
            return JsonResponse({"error": "Order number required"}, status=400)
        
        # Get order
        order = Order.objects.get(order_number=order_number, user=current_user)
        payment = Payment.objects.filter(order=order).first()
        
        if not payment:
            return JsonResponse({"error": "Payment not found"}, status=404)
        
        # Verify with Cashfree
        from .cashfree_utils import cashfree
        
        cf_response = cashfree.verify_payment(payment.cashfree_order_id)
        
        if cf_response.get('success'):
            payment_status = cf_response.get('payment_status', '').upper()
            
            if payment_status == 'PAID':
                # Update payment
                payment.status = 'success'
                payment.transaction_data = cf_response.get('data', {})
                payment.save()
                
                # Update order
                order.payment_status = 'success'
                order.status = 'confirmed'
                order.save()
                
                # Clear cart
                try:
                    cart = Cart.objects.get(user=current_user)
                    CartItem.objects.filter(cart=cart).delete()
                except:
                    pass
                
                return JsonResponse({
                    "success": True,
                    "payment_status": "success",
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "message": "Payment verified successfully"
                })
            else:
                # Payment failed or pending
                payment.status = 'failed' if payment_status == 'FAILED' else 'pending'
                payment.transaction_data = cf_response.get('data', {})
                payment.save()
                
                order.payment_status = 'failed' if payment_status == 'FAILED' else 'pending'
                order.save()
                
                return JsonResponse({
                    "success": False,
                    "payment_status": payment_status.lower(),
                    "message": "Payment not completed"
                })
        else:
            return JsonResponse({
                "success": False,
                "error": "Failed to verify payment",
                "message": cf_response.get('message')
            }, status=400)
            
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def payment_webhook(request):
    """Handle Cashfree payment webhook"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    try:
        # Get webhook signature headers
        timestamp = request.headers.get('x-webhook-timestamp', '')
        signature = request.headers.get('x-webhook-signature', '')
        
        # Verify signature
        from .cashfree_utils import cashfree
        
        raw_body = request.body.decode('utf-8')
        
        if not cashfree.verify_webhook_signature(timestamp, raw_body, signature):
            return JsonResponse({"error": "Invalid signature"}, status=401)
        
        # Parse webhook data
        data = json.loads(raw_body)
        
        event_type = data.get('type')
        order_data = data.get('data', {}).get('order', {})
        order_id = order_data.get('order_id')
        
        if not order_id:
            return JsonResponse({"error": "Order ID not found"}, status=400)
        
        # Find payment by Cashfree order ID
        payment = Payment.objects.filter(cashfree_order_id=order_id).first()
        
        if not payment:
            return JsonResponse({"error": "Payment not found"}, status=404)
        
        order = payment.order
        
        # Handle different event types
        if event_type == 'PAYMENT_SUCCESS_WEBHOOK':
            payment.status = 'success'
            payment.transaction_data = order_data
            payment.save()
            
            order.payment_status = 'success'
            order.status = 'confirmed'
            order.save()
            
            # Clear cart
            try:
                cart = Cart.objects.get(user=order.user)
                CartItem.objects.filter(cart=cart).delete()
            except:
                pass
                
        elif event_type == 'PAYMENT_FAILED_WEBHOOK':
            payment.status = 'failed'
            payment.transaction_data = order_data
            payment.save()
            
            order.payment_status = 'failed'
            order.save()
        
        return JsonResponse({"success": True})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def get_user_orders(request):
    """Get all orders for the current user"""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        user_id = payload.get('user_id')
        current_user = AppUser.objects.get(pk=user_id)
    except:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        orders = Order.objects.filter(user=current_user).order_by('-created_at')
        
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            
            # Add payment info if exists
            payment = Payment.objects.filter(order=order).first()
            if payment:
                order_dict['payment'] = payment.to_dict()
            
            orders_data.append(order_dict)
        
        return JsonResponse({
            "success": True,
            "orders": orders_data
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def get_order_detail(request, order_id):
    """Get detailed information for a specific order"""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        payload = decode_jwt(token)
        user_id = payload.get('user_id')
        current_user = AppUser.objects.get(pk=user_id)
    except:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        order = Order.objects.get(id=order_id, user=current_user)
        
        order_dict = order.to_dict()
        
        # Add payment info
        payment = Payment.objects.filter(order=order).first()
        if payment:
            order_dict['payment'] = payment.to_dict()
        
        return JsonResponse({
            "success": True,
            "order": order_dict
        })
        
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def get_friends_purchased(request, product_id):
    """Get list of friends who purchased this product"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = decode_jwt(token)
        user_id = payload.get('user_id')
        current_user = AppUser.objects.get(pk=user_id)
    except:
        return JsonResponse({"error": "Invalid token"}, status=401)
    
    try:
        product = Product.objects.get(pk=product_id)
        
        # Get all users that current user follows
        following_ids = UserFollow.objects.filter(
            follower=current_user
        ).values_list('following_id', flat=True)
        
        # Get orders from following users that contain this product
        friend_orders = OrderItem.objects.filter(
            product=product,
            order__user_id__in=following_ids,
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).select_related('order__user').distinct()
        
        # Get unique users who purchased
        purchased_by = {}
        for order_item in friend_orders:
            user = order_item.order.user
            if user.id not in purchased_by:
                purchased_by[user.id] = {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'bio': user.bio,
                    'purchased_date': order_item.order.created_at.isoformat()
                }
        
        friends_list = list(purchased_by.values())
        
        return JsonResponse({
            "success": True,
            "count": len(friends_list),
            "friends": friends_list
        })
        
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ========== AI RECOMMENDATIONS ==========
from .recommender import (
    ContentBasedRecommender,
    CollaborativeFilteringRecommender,
    SocialRecommender,
    HybridRecommender,
    DataExporter
)
from django.views.decorators.cache import cache_page
from django.core.cache import cache


@csrf_exempt
def get_personalized_recommendations(request):
    """
    GET /api/recommendations/personalized/
    Returns personalized product recommendations using hybrid approach.
    Requires authentication.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    # Get current user
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    token = auth_header.split(" ")[1]
    payload = decode_jwt(token)
    
    if not payload or "error" in payload:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    user_id = payload.get("user_id")
    
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    try:
        # Get limit parameter
        limit = int(request.GET.get('limit', 20))
        limit = min(max(limit, 1), 50)  # Between 1 and 50
        
        # Check cache first
        cache_key = f'recommendations_user_{user_id}_limit_{limit}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return JsonResponse(cached_result)
        
        # Check if user has any interaction history
        user_history = DataExporter.get_user_history(user_id)
        
        if not user_history['all']:
            # New user - use cold start recommendations
            recommendations = HybridRecommender.get_cold_start_recommendations(top_n=limit)
        else:
            # Existing user - use personalized recommendations
            recommendations = HybridRecommender.get_personalized_recommendations(user_id, top_n=limit)
        
        result = {
            "success": True,
            "count": len(recommendations),
            "recommendations": recommendations,
            "user_has_history": bool(user_history['all'])
        }
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, result, 3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_similar_products(request, product_id):
    """
    GET /api/recommendations/similar/<product_id>/
    Returns products similar to the given product.
    Public endpoint - no authentication required.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        # Verify product exists
        product = Product.objects.get(id=product_id)
        
        # Get limit parameter
        limit = int(request.GET.get('limit', 10))
        limit = min(max(limit, 1), 20)  # Between 1 and 20
        
        # Check cache first
        cache_key = f'similar_products_{product_id}_limit_{limit}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return JsonResponse(cached_result)
        
        # Get similar products
        similar_items = ContentBasedRecommender.get_similar_products(product_id, top_n=limit)
        
        # Get full product details
        recommendations = []
        for item in similar_items:
            try:
                similar_product = Product.objects.get(id=item['product_id'])
                recommendations.append({
                    'product': similar_product.to_dict(),
                    'similarity_score': item['similarity_score']
                })
            except Product.DoesNotExist:
                continue
        
        result = {
            "success": True,
            "product_id": product_id,
            "product_title": product.title,
            "count": len(recommendations),
            "similar_products": recommendations
        }
        
        # Cache for 24 hours (86400 seconds) - similar products change less frequently
        cache.set(cache_key, result, 86400)
        
        return JsonResponse(result)
        
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_friends_trending(request):
    """
    GET /api/recommendations/friends-trending/
    Returns products trending among user's friends.
    Requires authentication.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    # Get current user
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    token = auth_header.split(" ")[1]
    payload = decode_jwt(token)
    
    if not payload or "error" in payload:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    user_id = payload.get("user_id")
    
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    try:
        # Get limit parameter
        limit = int(request.GET.get('limit', 15))
        limit = min(max(limit, 1), 30)  # Between 1 and 30
        
        # Check cache first
        cache_key = f'friends_trending_user_{user_id}_limit_{limit}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return JsonResponse(cached_result)
        
        # Get trending products among friends
        trending_items = SocialRecommender.get_trending_among_friends(user_id, top_n=limit)
        
        if not trending_items:
            result = {
                "success": True,
                "count": 0,
                "message": "No trending products among friends",
                "trending_products": []
            }
            # Cache empty results for 30 minutes
            cache.set(cache_key, result, 1800)
            return JsonResponse(result)
        
        # Get full product details
        recommendations = []
        for item in trending_items:
            try:
                product = Product.objects.get(id=item['product_id'])
                recommendations.append({
                    'product': product.to_dict(),
                    'trending_score': item['score']
                })
            except Product.DoesNotExist:
                continue
        
        result = {
            "success": True,
            "count": len(recommendations),
            "trending_products": recommendations
        }
        
        # Cache for 30 minutes (1800 seconds) - trending changes more frequently
        cache.set(cache_key, result, 1800)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_recommendation_stats(request):
    """
    GET /api/recommendations/stats/
    Returns statistics about the recommendation system.
    Admin only.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    # Get current user
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    token = auth_header.split(" ")[1]
    payload = decode_jwt(token)
    
    if not payload or "error" in payload:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    user_id = payload.get("user_id")
    
    try:
        user = AppUser.objects.get(id=user_id)
        
        # Check if user is admin
        if not user.is_staff:
            return JsonResponse({"error": "Admin access required"}, status=403)
        
        # Get recommendation stats
        from .recommender import get_recommendation_stats
        stats = get_recommendation_stats()
        
        return JsonResponse({
            "success": True,
            "stats": stats
        })
        
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def refresh_recommendation_cache(request):
    """
    POST /api/recommendations/refresh-cache/
    Rebuild feature vectors and clear cache.
    Admin only.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    # Get current user
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    token = auth_header.split(" ")[1]
    payload = decode_jwt(token)
    
    if not payload or "error" in payload:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    user_id = payload.get("user_id")
    
    try:
        user = AppUser.objects.get(id=user_id)
        
        # Check if user is admin
        if not user.is_staff:
            return JsonResponse({"error": "Admin access required"}, status=403)
        
        # Rebuild feature vectors
        from .recommender import ProductFeatureVector
        from django.core.cache import cache
        
        ProductFeatureVector.build_feature_vectors()
        cache.clear()
        
        return JsonResponse({
            "success": True,
            "message": "Recommendation cache refreshed successfully"
        })
        
    except AppUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
