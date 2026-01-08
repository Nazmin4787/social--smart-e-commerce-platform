from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.list_products),
    path('products/create/', views.create_product),
    path('products/share/', views.share_product),  # MUST come before <str:product_id>
    path('products/<str:product_id>/friends-purchased/', views.get_friends_purchased),
    path('products/<str:product_id>/', views.get_product),
    path('auth/register/', views.register),
    path('auth/login/', views.login),
    path('auth/refresh/', views.refresh_token),
    path('cart/add/', views.add_to_cart),
    path('cart/', views.get_cart),
    path('cart/update/', views.update_cart_item),
    path('cart/item/<int:product_id>/remove/', views.remove_cart_item),
    path('orders/create/', views.create_order),
    path('bookings/create/', views.create_booking),
    path('bookings/', views.get_bookings),
    path('bookings/<int:booking_id>/', views.get_booking),
    
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
    path('liked-products/toggle/', views.toggle_like_product),
    path('liked-products/like/', views.like_product),
    path('liked-products/<int:product_id>/unlike/', views.unlike_product),
    
    # About Us
    path('about-us/', views.about_us),
    # Banners
    path('banners/', views.get_banners),
    path('admin/banners/', views.admin_banners),
    # Admin Orders
    path('admin/orders/', views.admin_orders),
    path('admin/orders/<int:order_id>/status/', views.admin_update_order_status),
    # Admin products
    path('admin/products/list/', views.admin_products_list),
    path('admin/products/<int:product_id>/stock/', views.admin_update_product_stock),
    path('admin/products/<int:product_id>/update/', views.admin_product_update),
    path('admin/products/<int:product_id>/delete/', views.admin_product_delete),
    path('admin/products/bulk-update/', views.admin_bulk_update_stock),
    # Admin dashboard
    path('admin/dashboard/', views.admin_dashboard),
    path('admin/dashboard/recent-orders/', views.admin_recent_orders),
    path('admin/dashboard/low-stock/', views.admin_low_stock),
    path('admin/dashboard/top-products/', views.admin_top_selling),
    # Reviews
    path('products/<int:product_id>/reviews/', views.get_reviews),
    path('products/<int:product_id>/reviews/create/', views.add_review),
    
    # ========== SOCIAL FEATURES ==========
    # Follow/Unfollow
    path('social/follow/<int:user_id>/', views.follow_user),
    path('social/unfollow/<int:user_id>/', views.unfollow_user),
    
    # Followers & Following
    path('social/followers/<int:user_id>/', views.get_followers),
    path('social/following/<int:user_id>/', views.get_following),
    path('social/users/<int:user_id>/mutual-followers/', views.get_mutual_followers),
    
    # User Profile & Discovery
    path('social/users/<int:user_id>/profile/', views.get_user_profile_social),
    path('social/users/search/', views.search_users),
    path('social/users/suggested/', views.get_suggested_users),
    
    # Notifications
    path('social/notifications/', views.get_notifications),
    path('social/notifications/<int:notification_id>/read/', views.mark_notification_read),
    path('social/notifications/mark-all-read/', views.mark_all_notifications_read),
    path('social/notifications/unread-count/', views.get_unread_notifications_count),
    
    # Friends' Product Activities
    path('social/friends-activities/', views.get_friends_product_activities),
    
    # Chat / Messaging
    path('chat/conversations/', views.get_conversations),
    path('chat/conversations/<int:other_user_id>/', views.get_or_create_conversation),
    path('chat/messages/<int:conversation_id>/', views.get_messages),
    path('chat/messages/<int:conversation_id>/send/', views.send_message),
    path('chat/messages/<int:message_id>/edit/', views.edit_message),
    path('chat/messages/<int:message_id>/delete/', views.delete_message),
    path('chat/unread-count/', views.get_unread_messages_count),
    
    # Allergy Management
    path('allergies/check/<int:product_id>/', views.check_product_allergies),
    path('allergies/check-cart/', views.check_cart_allergies),
    path('allergies/update/', views.update_user_allergies),
    
    # Wallet
    path('wallet/balance/', views.get_wallet_balance),
    path('wallet/add-money/', views.add_money_to_wallet),
    path('wallet/transactions/', views.get_wallet_transactions),
    path('wallet/pay-order/', views.create_order_with_wallet),
    
    # ========== PAYMENT & ORDERS ==========
    # Payment
    path('payment/create-order/', views.create_payment_order),
    path('payment/retry-order/', views.retry_payment_order),
    path('payment/verify/', views.verify_payment),
    path('payment/webhook/', views.payment_webhook),
    path('payment/quick-buy/', views.quick_buy),
    
    # Orders
    path('orders/my-orders/', views.get_user_orders),
    path('orders/<int:order_id>/', views.get_order_detail),
    
    # ========== AI RECOMMENDATIONS ==========
    path('recommendations/personalized/', views.get_personalized_recommendations),
    path('recommendations/similar/<int:product_id>/', views.get_similar_products),
    path('recommendations/friends-trending/', views.get_friends_trending),
    path('recommendations/stats/', views.get_recommendation_stats),
    path('recommendations/refresh-cache/', views.refresh_recommendation_cache),
]