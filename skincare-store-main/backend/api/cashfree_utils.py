import hashlib
import hmac
import json
import requests
from django.conf import settings
from decimal import Decimal


class CashfreePayment:
    """Cashfree Payment Gateway Integration"""
    
    def __init__(self):
        # Get credentials from settings, with fallback to demo credentials
        self.app_id = getattr(settings, 'CASHFREE_APP_ID', 'TEST_APP_ID')
        self.secret_key = getattr(settings, 'CASHFREE_SECRET_KEY', 'TEST_SECRET_KEY')
        # Use the correct sandbox URL
        self.base_url = 'https://sandbox.cashfree.com/pg'
        
    def create_order(self, order_id, order_amount, customer_details, order_meta):
        """
        Create a Cashfree order
        
        Args:
            order_id: Unique order ID from your system
            order_amount: Order amount (Decimal or float)
            customer_details: Dict with customer_id, customer_email, customer_phone
            order_meta: Dict with return_url and notify_url
            
        Returns:
            Dict with payment_session_id and order details
        """
        url = f"{self.base_url}/orders"
        
        headers = {
            'x-api-version': '2023-08-01',
            'x-client-id': self.app_id,
            'x-client-secret': self.secret_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Ensure customer phone has proper format (10 digits)
        customer_phone = customer_details.get('customer_phone', '9999999999')
        if len(customer_phone) < 10:
            customer_phone = '9999999999'
        
        payload = {
            'order_id': str(order_id),
            'order_amount': float(order_amount),
            'order_currency': 'INR',
            'customer_details': {
                'customer_id': str(customer_details.get('customer_id')),
                'customer_email': customer_details.get('customer_email'),
                'customer_phone': customer_phone
            },
            'order_meta': {
                'return_url': order_meta.get('return_url'),
                'notify_url': order_meta.get('notify_url')
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'payment_session_id': data.get('payment_session_id'),
                'order_id': data.get('order_id'),
                'order_status': data.get('order_status'),
                'data': data
            }
        except requests.exceptions.RequestException as e:
            # Get detailed error message
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', str(e))
                except:
                    error_msg = e.response.text if hasattr(e.response, 'text') else str(e)
            
            print(f"Cashfree API Error: {error_msg}")  # Log for debugging
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create payment order: {error_msg}'
            }
    
    def verify_payment(self, order_id):
        """
        Verify payment status from Cashfree
        
        Args:
            order_id: Cashfree order ID
            
        Returns:
            Dict with payment status and details
        """
        url = f"{self.base_url}/orders/{order_id}"
        
        headers = {
            'x-api-version': '2022-09-01',
            'x-client-id': self.app_id,
            'x-client-secret': self.secret_key,
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'order_status': data.get('order_status'),
                'payment_status': data.get('order_status'),
                'data': data
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to verify payment'
            }
    
    def verify_webhook_signature(self, timestamp, raw_body, signature):
        """
        Verify Cashfree webhook signature
        
        Args:
            timestamp: Timestamp from webhook header
            raw_body: Raw request body
            signature: Signature from webhook header
            
        Returns:
            Boolean indicating if signature is valid
        """
        try:
            # Construct the signature data
            signature_data = f"{timestamp}{raw_body}"
            
            # Compute HMAC SHA256
            computed_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(computed_signature, signature)
        except Exception:
            return False
    
    def get_payment_link(self, payment_session_id):
        """
        Get Cashfree payment link
        
        Args:
            payment_session_id: Session ID from create_order
            
        Returns:
            Payment link URL
        """
        return f"{self.base_url}/checkout?payment_session_id={payment_session_id}"


# Initialize singleton instance
cashfree = CashfreePayment()
