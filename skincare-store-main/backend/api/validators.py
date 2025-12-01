"""
Input validation utilities for API endpoints.
"""
import re
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError


def validate_email(email):
    """Validate email format."""
    try:
        django_validate_email(email)
        return True, None
    except ValidationError:
        return False, "Invalid email format"


def validate_password(password):
    """Validate password strength."""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, None


def validate_price(price):
    """Validate product price."""
    try:
        price_float = float(price)
        if price_float < 0:
            return False, "Price cannot be negative"
        if price_float > 1000000:
            return False, "Price is too high"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid price format"


def validate_quantity(quantity):
    """Validate quantity/stock."""
    try:
        qty_int = int(quantity)
        if qty_int < 0:
            return False, "Quantity cannot be negative"
        if qty_int > 100000:
            return False, "Quantity is too high"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid quantity format"


def validate_name(name):
    """Validate user name."""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters"
    if len(name) > 200:
        return False, "Name is too long"
    return True, None


def sanitize_string(text, max_length=None):
    """Sanitize string input to prevent XSS."""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = str(text).strip()
    
    # Remove HTML tags (basic sanitization)
    text = re.sub(r'<[^>]+>', '', text)
    
    if max_length:
        text = text[:max_length]
    
    return text


def validate_product_data(data):
    """Validate product creation/update data."""
    errors = []
    
    # Validate title
    title = data.get('title', '').strip()
    if not title or len(title) < 3:
        errors.append("Product title must be at least 3 characters")
    
    # Validate price
    price = data.get('price')
    if price is not None:
        valid, msg = validate_price(price)
        if not valid:
            errors.append(msg)
    else:
        errors.append("Price is required")
    
    # Validate stock
    stock = data.get('stock', 0)
    valid, msg = validate_quantity(stock)
    if not valid:
        errors.append(msg)
    
    return len(errors) == 0, errors


def validate_user_registration(data):
    """Validate user registration data."""
    errors = []
    
    # Validate name
    name = data.get('name', '').strip()
    valid, msg = validate_name(name)
    if not valid:
        errors.append(msg)
    
    # Validate email
    email = data.get('email', '').strip()
    valid, msg = validate_email(email)
    if not valid:
        errors.append(msg)
    
    # Validate password
    password = data.get('password', '')
    valid, msg = validate_password(password)
    if not valid:
        errors.append(msg)
    
    return len(errors) == 0, errors


def validate_phone(phone):
    """Validate phone number format."""
    if not phone or len(phone.strip()) < 10:
        return False, "Phone number must be at least 10 characters"
    # Allow digits, spaces, parentheses, hyphens, plus sign
    if not re.match(r'^[\d\s\(\)\-\+]+$', phone):
        return False, "Invalid phone number format"
    return True, None


def validate_postal_code(postal_code):
    """Validate postal code."""
    if not postal_code or len(postal_code.strip()) < 3:
        return False, "Postal code must be at least 3 characters"
    if len(postal_code) > 20:
        return False, "Postal code is too long"
    return True, None


def validate_address_data(data):
    """Validate address creation/update data."""
    errors = []
    
    # Validate address type
    address_type = data.get('address_type', '').strip()
    if address_type not in ['shipping', 'billing']:
        errors.append("Address type must be 'shipping' or 'billing'")
    
    # Validate full name
    full_name = data.get('full_name', '').strip()
    valid, msg = validate_name(full_name)
    if not valid:
        errors.append(f"Full name: {msg}")
    
    # Validate phone
    phone = data.get('phone', '').strip()
    valid, msg = validate_phone(phone)
    if not valid:
        errors.append(msg)
    
    # Validate address line 1
    address_line1 = data.get('address_line1', '').strip()
    if not address_line1 or len(address_line1) < 5:
        errors.append("Address line 1 must be at least 5 characters")
    
    # Validate city
    city = data.get('city', '').strip()
    if not city or len(city) < 2:
        errors.append("City must be at least 2 characters")
    
    # Validate state
    state = data.get('state', '').strip()
    if not state or len(state) < 2:
        errors.append("State must be at least 2 characters")
    
    # Validate postal code
    postal_code = data.get('postal_code', '').strip()
    valid, msg = validate_postal_code(postal_code)
    if not valid:
        errors.append(msg)
    
    # Validate country
    country = data.get('country', '').strip()
    if not country or len(country) < 2:
        errors.append("Country must be at least 2 characters")
    
    return len(errors) == 0, errors
