from django.contrib import admin
from django.utils.html import format_html
from .models import Banner
from .models import Order, OrderItem, Address


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
    list_display = ('title', 'is_active', 'position', 'created_at', 'image_preview')
    list_filter = ('is_active',)
    search_fields = ('title', 'link')
    ordering = ('position', '-created_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px;"/>', obj.image.url)
        return ''

    image_preview.short_description = 'Image'
