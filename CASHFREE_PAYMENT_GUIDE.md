# Cashfree Payment Integration Guide

## Overview
This document explains the Cashfree payment gateway integration with wallet and cash-on-delivery options for the e-commerce platform.

## Features Implemented

### 1. **Payment Methods**
- **Cashfree Payment Gateway**: Credit/Debit cards, UPI, Net Banking
- **Wallet Payment**: Use existing wallet balance
- **Cash on Delivery (COD)**: Pay when you receive the product

### 2. **Order Management**
- View all orders with status tracking
- Detailed order information
- Order tracking numbers
- Amazon-like order history interface

### 3. **Order Statuses**
- Pending
- Confirmed  
- Processing
- Shipped
- Delivered
- Cancelled
- Refunded

## Backend Setup

### 1. Models Created
- **Order**: Enhanced with order_number, payment_status, shipping/billing addresses, tracking number
- **Payment**: Tracks payment transactions with Cashfree integration

### 2. API Endpoints
```
POST /api/payment/create-order/ - Create payment order
POST /api/payment/verify/ - Verify payment status
POST /api/payment/webhook/ - Cashfree webhook handler
GET /api/orders/my-orders/ - Get user's orders
GET /api/orders/<id>/ - Get specific order details
```

### 3. Cashfree Configuration

Add these to your `.env` file:
```bash
# Cashfree Payment Gateway
CASHFREE_APP_ID=your_app_id_here
CASHFREE_SECRET_KEY=your_secret_key_here
CASHFREE_BASE_URL=https://sandbox.cashfree.com/pg  # Use sandbox for testing
```

For production:
```bash
CASHFREE_BASE_URL=https://api.cashfree.com/pg
```

### 4. Get Cashfree Credentials

1. Sign up at [Cashfree](https://www.cashfree.com/)
2. Go to Dashboard → Developers → Credentials
3. Copy your APP ID and SECRET KEY
4. For testing, use Sandbox credentials
5. For production, use Production credentials

## Frontend Setup

### 1. New Pages Created
- `/checkout` - Checkout page with address and payment selection
- `/orders` - List of all user orders
- `/orders/:id` - Detailed order information
- `/payment/success` - Payment success handling

### 2. Payment Flow

```
Cart → Checkout → Select Address → Choose Payment → Place Order
                                                      ↓
                   ← Payment Success ← Cashfree Gateway (for online payment)
                   ↓
              Order Confirmation
```

### 3. Testing the Payment Flow

#### Test with Cash on Delivery:
1. Add products to cart
2. Go to checkout
3. Select shipping address
4. Choose "Cash on Delivery"
5. Place order
6. Order is confirmed immediately

#### Test with Wallet:
1. Add money to wallet first
2. Add products to cart
3. Go to checkout  
4. Select shipping address
5. Choose "Wallet"
6. Place order (wallet balance deducted)
7. Order is confirmed immediately

#### Test with Cashfree (Sandbox):
1. Add products to cart
2. Go to checkout
3. Select shipping and billing addresses
4. Choose "Cashfree Payment Gateway"
5. Click "Place Order"
6. You'll be redirected to Cashfree checkout
7. Use test card details:
   - Card Number: 4111 1111 1111 1111
   - CVV: 123
   - Expiry: Any future date
8. Complete payment
9. Redirected back to order confirmation

## Database Migrations

Run these commands to apply the new models:

```bash
cd backend
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

## Usage Instructions

### For Users:

1. **Checkout Process**:
   - View cart and click "Proceed to Checkout"
   - Select or add shipping address
   - Choose payment method
   - Review and place order

2. **View Orders**:
   - Click "Orders" in navigation
   - See all past orders with status
   - Click any order for details

3. **Track Orders**:
   - Order status updates automatically
   - Tracking number shown when shipped
   - Payment status visible

### For Admin:

Admins can:
- View all orders in admin panel
- Update order status
- Add tracking numbers
- Manage payments

## Security Features

1. **Payment Verification**: All payments verified with Cashfree API
2. **Webhook Signature**: Validates webhook authenticity
3. **Token Authentication**: All endpoints require valid JWT
4. **HTTPS Required**: Production must use HTTPS

## Troubleshooting

### Payment Not Working?
1. Check Cashfree credentials in `.env`
2. Verify you're using correct sandbox/production URL
3. Check browser console for errors
4. Ensure Django backend is running

### Orders Not Showing?
1. Check if migrations are applied
2. Verify user is logged in
3. Check API endpoints are accessible

### Webhooks Not Received?
1. Cashfree webhooks need public URL
2. Use ngrok for local testing:
   ```bash
   ngrok http 8000
   ```
3. Add ngrok URL to Cashfree dashboard

## File Structure

```
backend/
├── api/
│   ├── models.py (Order, Payment models)
│   ├── views.py (payment endpoints)
│   ├── urls.py (routes)
│   └── cashfree_utils.py (Cashfree SDK wrapper)
└── skincare_backend/
    └── settings.py (Cashfree config)

frontend/
├── src/
│   ├── api.js (payment API functions)
│   ├── App.js (routes)
│   ├── pages/
│   │   ├── CheckoutPage.js
│   │   ├── OrdersPage.js
│   │   └── OrderDetailPage.js
│   └── styles.css (payment page styles)
```

## Next Steps

1. **Test thoroughly** with sandbox credentials
2. **Add addresses** in profile before checkout
3. **Top up wallet** for wallet payments
4. **Get production credentials** from Cashfree
5. **Deploy to production** with HTTPS

## Support

For Cashfree API documentation:
- [Cashfree Docs](https://docs.cashfree.com/docs)
- [Cashfree API Reference](https://docs.cashfree.com/reference)

For integration issues:
- Check Django logs
- Check browser console
- Verify API responses
