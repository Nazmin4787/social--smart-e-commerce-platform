from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.list_products),
    path('products/create/', views.create_product),
    path('products/<str:product_id>/', views.get_product),
    path('auth/register/', views.register),
    path('auth/login/', views.login),
    path('auth/refresh/', views.refresh_token),
    path('cart/add/', views.add_to_cart),
    path('cart/', views.get_cart),
    path('orders/create/', views.create_order),
    
    # User Profile
    path('profile/', views.get_user_profile),
    path('profile/update/', views.update_user_profile),
    
    # Addresses
    path('addresses/', views.get_addresses),
    path('addresses/create/', views.create_address),
    path('addresses/<int:address_id>/', views.update_address),
    path('addresses/<int:address_id>/delete/', views.delete_address),
    
    # Password Change
    path('auth/change-password/', views.change_password),
    
    # My Orders
    path('orders/', views.get_my_orders),
    
    # Liked Products
    path('liked-products/', views.get_liked_products),
    path('liked-products/like/', views.like_product),
    path('liked-products/<int:product_id>/unlike/', views.unlike_product),
    
    # About Us
    path('about-us/', views.about_us),
]
