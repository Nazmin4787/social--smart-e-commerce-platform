from django.contrib import admin
from django.utils.html import format_html
from .models import Banner, UserFollow, Notification, ProductShare
from .models import Order, OrderItem, Address, Product, AppUser, Wallet, WalletTransaction


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'qty', 'price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'total', 'status', 'created_at', 'shipping_address_short')
    list_filter = ('status', ('created_at', admin.DateFieldListFilter), 'user')
    search_fields = ('user__name', 'user__email', 'id')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    readonly_fields = ('shipping_address',)

    def customer_name(self, obj):
        return obj.user.name if obj.user else ''

    def customer_email(self, obj):
        return obj.user.email if obj.user else ''

    def shipping_address(self, obj):
        # Try to return default address for the user or latest address
        if not obj.user:
            return ''
        addr = Address.objects.filter(user=obj.user).order_by('-is_default', '-created_at').first()
        if not addr:
            return ''
        parts = [addr.full_name, addr.phone, addr.address_line1, addr.address_line2, addr.city, addr.state, addr.postal_code, addr.country]
        return ', '.join([p for p in parts if p])

    def shipping_address_short(self, obj):
        a = self.shipping_address(obj)
        return (a[:75] + '...') if a and len(a) > 75 else a

    shipping_address.short_description = 'Shipping address'
    shipping_address_short.short_description = 'Shipping'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'banner_type', 'is_active', 'order', 'created_at', 'image_preview')
    list_filter = ('is_active', 'banner_type', 'created_at')
    search_fields = ('title', 'description', 'link_url')
    ordering = ('order', '-created_at')
    list_editable = ('is_active', 'order')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'banner_type', 'description')
        }),
        ('Image', {
            'fields': ('image', 'image_preview_large')
        }),
        ('Settings', {
            'fields': ('link_url', 'is_active', 'order')
        }),
    )
    
    readonly_fields = ('image_preview_large', 'created_at', 'updated_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px; border-radius:4px;"/>', obj.image.url)
        return format_html('<span style="color:#999;">No image</span>')
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:500px; max-height:300px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>',
                obj.image.url
            )
        return format_html('<p style="color:#999;">No image uploaded</p>')

    image_preview.short_description = 'Preview'
    image_preview_large.short_description = 'Image Preview'


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower_name', 'following_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__name', 'follower__email', 'following__name', 'following__email')
    ordering = ('-created_at',)
    readonly_fields = ('follower', 'following', 'created_at')
    
    def follower_name(self, obj):
        return f"{obj.follower.name} ({obj.follower.email})"
    
    def following_name(self, obj):
        return f"{obj.following.name} ({obj.following.email})"
    
    follower_name.short_description = 'Follower'
    following_name.short_description = 'Following'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_name', 'actor_name', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__name', 'user__email', 'actor__name', 'actor__email', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'actor', 'notification_type', 'message', 'created_at')
    actions = ['mark_as_read', 'mark_as_unread']
    
    def user_name(self, obj):
        return f"{obj.user.name} ({obj.user.email})"
    
    def actor_name(self, obj):
        return f"{obj.actor.name} ({obj.actor.email})"
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notifications marked as read.")
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notifications marked as unread.")
    
    user_name.short_description = 'User'
    actor_name.short_description = 'Actor'
    mark_as_read.short_description = "Mark selected as read"
    mark_as_unread.short_description = "Mark selected as unread"


@admin.register(ProductShare)
class ProductShareAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_title', 'sender_name', 'recipient_name', 'is_viewed', 'created_at')
    list_filter = ('is_viewed', 'created_at')
    search_fields = ('product__title', 'sender__name', 'sender__email', 'recipient__name', 'recipient__email', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('product', 'sender', 'recipient', 'message', 'created_at')
    
    def product_title(self, obj):
        return obj.product.title
    
    def sender_name(self, obj):
        return f"{obj.sender.name} ({obj.sender.email})"
    
    def recipient_name(self, obj):
        return f"{obj.recipient.name} ({obj.recipient.email})"
    
    product_title.short_description = 'Product'
    sender_name.short_description = 'Sender'
    recipient_name.short_description = 'Recipient'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'price', 'stock', 'ingredient_count', 'created_info')
    list_filter = ('category', 'stock')
    search_fields = ('title', 'description', 'category')
    ordering = ('-id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock')
        }),
        ('Product Images', {
            'fields': ('images',),
            'description': 'Add product image URLs as a JSON array. Example: ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]'
        }),
        ('Ingredients (For Allergy Tracking)', {
            'fields': ('ingredients',),
            'description': 'Add ingredients as a JSON array. Example: ["Parabens", "Sulfates", "Fragrance", "Retinol"]. This helps users with allergies avoid harmful products.'
        }),
    )
    
    def ingredient_count(self, obj):
        count = len(obj.ingredients) if obj.ingredients else 0
        if count == 0:
            return format_html('<span style="color: orange;">⚠ No ingredients</span>')
        return format_html('<span style="color: green;">✓ {} ingredients</span>', count)
    
    def created_info(self, obj):
        return "Product entry"
    
    ingredient_count.short_description = 'Ingredients'
    created_info.short_description = 'Info'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'allergy_count', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('name', 'email')
    ordering = ('-id',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('name', 'email', 'password', 'bio')
        }),
        ('Allergies & Preferences', {
            'fields': ('allergies',),
            'description': 'User\'s allergies/ingredients to avoid. Stored as JSON array.'
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser')
        }),
    )
    
    readonly_fields = ('password',)
    
    def allergy_count(self, obj):
        count = len(obj.allergies) if obj.allergies else 0
        if count == 0:
            return format_html('<span style="color: gray;">No allergies</span>')
        return format_html('<span style="color: #1B5E47;">✓ {} allergies</span>', count)
    
    allergy_count.short_description = 'Allergies'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_name', 'balance_display', 'transaction_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__name', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'created_at', 'updated_at')
    
    def user_name(self, obj):
        return f"{obj.user.name} ({obj.user.email})"
    
    def balance_display(self, obj):
        return format_html('<span style="font-weight:bold; color:#047857;">₹{}</span>', obj.balance)
    
    def transaction_count(self, obj):
        count = obj.transactions.count()
        return format_html('<span>{} transactions</span>', count)
    
    user_name.short_description = 'User'
    balance_display.short_description = 'Balance'
    transaction_count.short_description = 'Transactions'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet_user', 'transaction_type', 'amount_display', 'status', 'description_short', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('wallet__user__name', 'wallet__user__email', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('wallet', 'transaction_type', 'amount', 'status', 'description', 'order', 'created_at')
    
    def wallet_user(self, obj):
        return f"{obj.wallet.user.name}"
    
    def amount_display(self, obj):
        color = '#047857' if obj.transaction_type == 'credit' else '#dc2626'
        prefix = '+' if obj.transaction_type == 'credit' else '-'
        return format_html('<span style="font-weight:bold; color:{};">{} ₹{}</span>', color, prefix, obj.amount)
    
    def description_short(self, obj):
        return (obj.description[:50] + '...') if len(obj.description) > 50 else obj.description
    
    wallet_user.short_description = 'User'
    amount_display.short_description = 'Amount'
    description_short.short_description = 'Description'
