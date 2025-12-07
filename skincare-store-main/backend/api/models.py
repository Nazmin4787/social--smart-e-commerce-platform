from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, default='general')
    ingredients = models.JSONField(default=list, blank=True)  # List of ingredients

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': float(self.price),
            'stock': self.stock,
            'images': self.images,
            'category': self.category,
            'ingredients': self.ingredients,
            'average_rating': self.average_rating(),
            'reviews': [r.to_dict() for r in getattr(self, 'reviews_cache', self.reviews.all())[:10]] if hasattr(self, 'reviews') else [],
        }


class AppUser(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    bio = models.TextField(blank=True, default='')
    allergies = models.JSONField(default=list, blank=True)  # List of allergies
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)
        
    def check_password(self, raw_password):
        """Check if the provided password matches the hashed password."""
        return check_password(raw_password, self.password)

    def get_followers_count(self):
        """Get the count of users following this user."""
        return self.followers.count()
    
    def get_following_count(self):
        """Get the count of users this user is following."""
        return self.following.count()
    
    def is_following(self, user_id):
        """Check if this user is following another user."""
        return self.following.filter(following_id=user_id).exists()
    
    def get_mutual_followers_count(self, other_user_id):
        """Get count of mutual followers between this user and another user."""
        # Users that follow both this user and the other user
        from django.db.models import Count
        return AppUser.objects.filter(
            following__following=self
        ).filter(
            following__following_id=other_user_id
        ).count()

    def to_dict(self):
        return {
            'id': self.id, 
            'name': self.name, 
            'email': self.email, 
            'bio': self.bio,
            'allergies': self.allergies,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser
        }
    
    def to_profile_dict(self, requesting_user=None):
        """Return detailed profile with social stats."""
        profile = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'bio': self.bio,
            'followers_count': self.get_followers_count(),
            'following_count': self.get_following_count(),
            'is_following': False,
            'mutual_followers_count': 0,
        }
        
        if requesting_user and requesting_user.id != self.id:
            profile['is_following'] = requesting_user.is_following(self.id)
            profile['mutual_followers_count'] = requesting_user.get_mutual_followers_count(self.id)
        
        return profile


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


class UserFollow(models.Model):
    """Model to track user follow relationships (Instagram-style)."""
    follower = models.ForeignKey(
        AppUser, 
        on_delete=models.CASCADE, 
        related_name='following',
        help_text="User who is following"
    )
    following = models.ForeignKey(
        AppUser, 
        on_delete=models.CASCADE, 
        related_name='followers',
        help_text="User being followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['follower', 'following']),
            models.Index(fields=['following']),
            models.Index(fields=['follower']),
        ]
    
    def to_dict(self):
        return {
            'id': self.id,
            'follower': self.follower.to_dict(),
            'following': self.following.to_dict(),
            'created_at': self.created_at.isoformat(),
        }
    
    def __str__(self):
        return f"{self.follower.name} follows {self.following.name}"


class Notification(models.Model):
    """Model to track social notifications."""
    NOTIFICATION_TYPES = [
        ('follow', 'Follow'),
    ]
    
    user = models.ForeignKey(
        AppUser, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        help_text="User receiving the notification"
    )
    actor = models.ForeignKey(
        AppUser, 
        on_delete=models.CASCADE, 
        related_name='actions',
        help_text="User who performed the action"
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def to_dict(self):
        return {
            'id': self.id,
            'actor': {
                'id': self.actor.id,
                'name': self.actor.name,
                'email': self.actor.email,
                'bio': self.actor.bio,
            },
            'notification_type': self.notification_type,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
        }
    
    def __str__(self):
        return f"{self.notification_type}: {self.actor.name} -> {self.user.name}"


# ============================================================================
# CHAT MODELS
# ============================================================================

class Conversation(models.Model):
    """Model for chat conversations between two users."""
    user1 = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='conversations_as_user1'
    )
    user2 = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='conversations_as_user2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user1', 'user2']),
            models.Index(fields=['-updated_at']),
        ]
    
    def get_other_user(self, current_user_id):
        """Get the other user in the conversation."""
        return self.user2 if self.user1.id == current_user_id else self.user1
    
    def get_last_message(self):
        """Get the last message in this conversation."""
        return self.messages.first()
    
    def to_dict(self, current_user_id):
        """Convert conversation to dictionary."""
        other_user = self.get_other_user(current_user_id)
        last_message = self.get_last_message()
        unread_count = self.messages.filter(is_read=False).exclude(sender_id=current_user_id).count()
        
        return {
            'id': self.id,
            'other_user': {
                'id': other_user.id,
                'name': other_user.name,
                'email': other_user.email,
            },
            'last_message': last_message.to_dict() if last_message else None,
            'unread_count': unread_count,
            'updated_at': self.updated_at.isoformat(),
            'created_at': self.created_at.isoformat(),
        }


class Message(models.Model):
    """Model for individual messages in a conversation."""
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('product', 'Product Share'),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    shared_product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shared_in_messages'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_read']),
        ]
    
    def to_dict(self):
        """Convert message to dictionary."""
        message_dict = {
            'id': self.id,
            'conversation_id': self.conversation.id,
            'sender': {
                'id': self.sender.id,
                'name': self.sender.name,
            },
            'content': self.content,
            'message_type': self.message_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
        }
        
        # Include product details if this is a product share
        if self.message_type == 'product' and self.shared_product:
            message_dict['shared_product'] = {
                'id': self.shared_product.id,
                'title': self.shared_product.title,
                'price': float(self.shared_product.price),
                'images': self.shared_product.images,
                'stock': self.shared_product.stock,
            }
        
        return message_dict


# ============================================================================
# PRODUCT SHARE MODEL
# ============================================================================

class ProductShare(models.Model):
    """Model for sharing products between users."""
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='shares'
    )
    sender = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='shared_products'
    )
    recipient = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='received_shares'
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_viewed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['product']),
        ]
    
    def to_dict(self):
        """Convert share to dictionary."""
        return {
            'id': self.id,
            'product': {
                'id': self.product.id,
                'title': self.product.title,
                'price': float(self.product.price),
                'images': self.product.images,
            },
            'sender': {
                'id': self.sender.id,
                'name': self.sender.name,
            },
            'recipient': {
                'id': self.recipient.id,
                'name': self.recipient.name,
            },
            'message': self.message,
            'is_viewed': self.is_viewed,
            'created_at': self.created_at.isoformat(),
        }


class Banner(models.Model):
    """Model for managing homepage banners and promotional images"""
    BANNER_TYPES = [
        ('hero', 'Hero Banner'),
        ('featured', 'Featured Products Banner'),
        ('category', 'Category Banner'),
        ('promotional', 'Promotional Banner'),
    ]
    
    title = models.CharField(max_length=255)
    banner_type = models.CharField(max_length=50, choices=BANNER_TYPES, default='featured')
    image = models.ImageField(upload_to='banners/', null=True, blank=True)
    description = models.TextField(blank=True)
    link_url = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
    
    def __str__(self):
        return f"{self.title} ({self.get_banner_type_display()})"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'banner_type': self.banner_type,
            'image': self.image.url if self.image else None,
            'description': self.description,
            'link_url': self.link_url,
            'is_active': self.is_active,
            'order': self.order,
        }
