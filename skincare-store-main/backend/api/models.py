from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, default='general')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': float(self.price),
            'stock': self.stock,
            'images': self.images,
            'category': self.category,
            'average_rating': self.average_rating(),
            'reviews': [r.to_dict() for r in getattr(self, 'reviews_cache', self.reviews.all())[:10]] if hasattr(self, 'reviews') else [],
        }


class AppUser(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    bio = models.TextField(blank=True, default='')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)
        
    def check_password(self, raw_password):
        """Check if the provided password matches the hashed password."""
        return check_password(raw_password, self.password)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email, 'bio': self.bio}


class Cart(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, related_name='cart')


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)


class Order(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='created')
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


class Address(models.Model):
    ADDRESS_TYPES = [
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
    ]
    
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Addresses'
    
    def to_dict(self):
        return {
            'id': self.id,
            'address_type': self.address_type,
            'full_name': self.full_name,
            'phone': self.phone,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'is_default': self.is_default,
        }


class UserLikedProduct(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='liked_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='liked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
    
    def to_dict(self):
        return {
            'id': self.id,
            'product': self.product.to_dict(),
            'liked_at': self.created_at.isoformat()
        }


class Review(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'id': self.id,
            'user': {'id': self.user.id, 'name': self.user.name},
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat(),
        }


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='bookings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    qty = models.IntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-booking_date']

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user.id,
            'product': self.product.to_dict(),
            'booking_date': self.booking_date.isoformat(),
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'status': self.status,
            'payment_status': self.payment_status,
            'qty': self.qty,
            'notes': self.notes,
        }

    def __str__(self):
        return f"Booking {self.id} - {self.product.title} for {self.user.email}"


class Banner(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', '-created_at']

    def to_dict(self, request=None):
        img_url = None
        if self.image:
            try:
                if request is not None:
                    img_url = request.build_absolute_uri(self.image.url)
                else:
                    img_url = self.image.url
            except Exception:
                img_url = getattr(self.image, 'url', None)

        return {
            'id': self.id,
            'title': self.title,
            'image': img_url,
            'link': self.link,
            'is_active': self.is_active,
            'position': self.position,
            'created_at': self.created_at.isoformat(),
        }

def product_average_rating(product):
    qs = product.reviews.all()
    if not qs.exists():
        return None
    return round(sum([r.rating for r in qs]) / qs.count(), 2)

def Product_average_rating(self):
    return product_average_rating(self)

Product.average_rating = Product_average_rating
