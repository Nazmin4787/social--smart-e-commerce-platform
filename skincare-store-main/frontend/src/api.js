import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';
export const API_URL = API_BASE;

// Helper function to get auth headers
const getAuthHeaders = (token) => ({
  headers: { 'Authorization': `Bearer ${token}` }
});

// Setup axios interceptor for automatic token refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if it's a 401 error and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      const errorMessage = error.response?.data?.error || '';
      
      // Only try to refresh if it's a token expiration issue
      if (errorMessage.includes('expired') || errorMessage.includes('Invalid token')) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          }).then(token => {
            originalRequest.headers['Authorization'] = 'Bearer ' + token;
            return axios(originalRequest);
          }).catch(err => {
            return Promise.reject(err);
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const refreshToken = localStorage.getItem('refreshToken') || localStorage.getItem('refresh_token');
        
        if (!refreshToken) {
          // No refresh token, logout user
          localStorage.clear();
          window.location.href = '/';
          return Promise.reject(error);
        }

        try {
          const response = await axios.post(`${API_BASE}/auth/refresh/`, {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          
          // Update tokens in localStorage
          localStorage.setItem('accessToken', access_token);
          localStorage.setItem('access_token', access_token);
          
          // Update the original request with new token
          originalRequest.headers['Authorization'] = 'Bearer ' + access_token;
          
          processQueue(null, access_token);
          
          return axios(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          
          // Refresh failed, logout user
          localStorage.clear();
          window.location.href = '/';
          
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }
    }

    return Promise.reject(error);
  }
);

// Products
export async function fetchProducts() {
  return axios.get(`${API_BASE}/products/`).then(r => r.data);
}

// Authentication
export async function register(name, email, password, allergies = []) {
  return axios.post(`${API_BASE}/auth/register/`, { name, email, password, allergies }).then(r => r.data);
}

export async function login(email, password) {
  return axios.post(`${API_BASE}/auth/login/`, { email, password }).then(r => r.data);
}

// Cart
export async function addToCart(token, productId, qty = 1) {
  return axios.post(
    `${API_BASE}/cart/add/`,
    { product_id: productId, qty },
    getAuthHeaders(token)
  ).then(r => r.data);
}

export async function getCart(token) {
  return axios.get(`${API_BASE}/cart/`, getAuthHeaders(token)).then(r => r.data);
}

export async function updateCartItem(token, productId, qty) {
  return axios.post(
    `${API_BASE}/cart/update/`,
    { product_id: productId, qty },
    getAuthHeaders(token)
  ).then(r => r.data);
}

export async function removeCartItem(token, productId) {
  return axios.delete(`${API_BASE}/cart/item/${productId}/remove/`, getAuthHeaders(token)).then(r => r.data);
}

// Orders
export async function createOrder(token, items, total) {
  return axios.post(
    `${API_BASE}/orders/create/`,
    { items, total },
    getAuthHeaders(token)
  ).then(r => r.data);
}

// Quick Buy (Book Now) - Creates order directly from product
export async function quickBuy(token, productId, qty = 1) {
  return axios.post(
    `${API_BASE}/payment/quick-buy/`,
    { product_id: productId, qty },
    getAuthHeaders(token)
  ).then(r => r.data);
}

// Bookings
export async function createBooking(token, productId, { qty = 1, delivery_date = null, notes = '', payment_status = 'pending' } = {}) {
  return axios.post(
    `${API_BASE}/bookings/create/`,
    { product_id: productId, qty, delivery_date, notes, payment_status },
    getAuthHeaders(token)
  ).then(r => r.data);
}

export async function getBookings(token) {
  return axios.get(`${API_BASE}/bookings/`, getAuthHeaders(token)).then(r => r.data);
}

// Reviews
export async function addReview(token, productId, rating, comment = '') {
  return axios.post(`${API_BASE}/products/${productId}/reviews/create/`, { rating, comment }, getAuthHeaders(token)).then(r => r.data);
}

export async function getReviews(productId) {
  return axios.get(`${API_BASE}/products/${productId}/reviews/`).then(r => r.data);
}

// Liked Products
export async function likeProduct(token, productId) {
  return axios.post(
    `${API_BASE}/liked-products/toggle/`,
    { product_id: productId },
    getAuthHeaders(token)
  ).then(r => r.data);
}

export async function getLikedProducts(token) {
  return axios.get(`${API_BASE}/liked-products/`, getAuthHeaders(token)).then(r => r.data);
}

// About Us
export async function getAboutUs() {
  return axios.get(`${API_BASE}/about-us/`).then(r => r.data);
}

// User Profile
export async function getProfile(token) {
  return axios.get(`${API_BASE}/profile/`, getAuthHeaders(token)).then(r => r.data);
}

export async function updateProfile(token, profileData) {
  return axios.put(`${API_BASE}/profile/update/`, profileData, getAuthHeaders(token)).then(r => r.data);
}

// Addresses
export async function getAddresses(token) {
  return axios.get(`${API_BASE}/addresses/`, getAuthHeaders(token)).then(r => r.data);
}

export async function createAddress(token, addressData) {
  return axios.post(`${API_BASE}/addresses/create/`, addressData, getAuthHeaders(token)).then(r => r.data);
}

export async function updateAddress(token, addressId, addressData) {
  return axios.put(`${API_BASE}/addresses/${addressId}/`, addressData, getAuthHeaders(token)).then(r => r.data);
}

export async function deleteAddress(token, addressId) {
  return axios.delete(`${API_BASE}/addresses/${addressId}/delete/`, getAuthHeaders(token)).then(r => r.data);
}

// Admin APIs
export async function getDashboardStats(token) {
  return axios.get(`${API_BASE}/admin/dashboard/`, getAuthHeaders(token)).then(r => r.data);
}

export async function getRecentOrders(token) {
  return axios.get(`${API_BASE}/admin/dashboard/recent-orders/`, getAuthHeaders(token)).then(r => r.data);
}

export async function getLowStock(token) {
  return axios.get(`${API_BASE}/admin/dashboard/low-stock/`, getAuthHeaders(token)).then(r => r.data);
}

export async function getTopProducts(token) {
  return axios.get(`${API_BASE}/admin/dashboard/top-products/`, getAuthHeaders(token)).then(r => r.data);
}

export async function getAllOrders(token) {
  return axios.get(`${API_BASE}/admin/orders/`, getAuthHeaders(token)).then(r => r.data);
}

export async function updateOrderStatus(token, orderId, status) {
  return axios.patch(`${API_BASE}/admin/orders/${orderId}/status/`, { status }, getAuthHeaders(token)).then(r => r.data);
}

export async function getAllProducts(token, page = 1, page_size = 100) {
  return axios.get(`${API_BASE}/admin/products/list/?page=${page}&page_size=${page_size}`, getAuthHeaders(token)).then(r => {
    // r.data contains: { total, page, page_size, results }
    console.log('API Response:', r.data);
    console.log('Results field:', r.data.results);
    console.log('Results length:', r.data.results?.length);
    return r.data.results || [];
  });
}

export async function updateProductStock(token, productId, stock) {
  return axios.patch(`${API_BASE}/admin/products/${productId}/stock/`, { stock }, getAuthHeaders(token)).then(r => r.data);
}

export async function bulkUpdateStock(token, updates) {
  return axios.post(`${API_BASE}/admin/products/bulk-update/`, { updates }, getAuthHeaders(token)).then(r => r.data);
}

export async function getBanners() {
  return axios.get(`${API_BASE}/banners/`).then(r => r.data.banners || r.data);
}

export async function createBanner(token, formData) {
  return axios.post(`${API_BASE}/admin/banners/`, formData, {
    ...getAuthHeaders(token),
    headers: {
      ...getAuthHeaders(token).headers,
      'Content-Type': 'multipart/form-data'
    }
  }).then(r => r.data);
}

export async function deleteBanner(token, bannerId) {
  return axios.delete(`${API_BASE}/admin/banners/`, {
    ...getAuthHeaders(token),
    data: { id: bannerId }
  }).then(r => r.data);
}

// Admin Product Management
export async function createProduct(token, productData) {
  // Don't set Content-Type manually - let axios set it for FormData (includes boundary)
  return axios.post(`${API_BASE}/products/create/`, productData, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }).then(r => r.data);
}

export async function updateProduct(token, productId, productData) {
  console.log('updateProduct called with productId:', productId);
  // Don't set Content-Type manually - let axios set it for FormData (includes boundary)
  return axios.put(`${API_BASE}/admin/products/${productId}/update/`, productData, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }).then(r => {
    console.log('updateProduct response:', r.data);
    return r.data;
  }).catch(err => {
    console.error('updateProduct error:', err.response?.data || err.message);
    throw err;
  });
}

export async function deleteProduct(token, productId) {
  return axios.delete(`${API_BASE}/admin/products/${productId}/delete/`, getAuthHeaders(token)).then(r => r.data);
}

export async function getProductById(productId) {
  return axios.get(`${API_BASE}/products/${productId}/`).then(r => r.data);
}

// ============================================================================
// PRODUCT SHARING
// ============================================================================
export async function shareProduct(token, productId, recipientId, message) {
  return axios.post(
    `${API_BASE}/products/share/`,
    {
      product_id: productId,
      recipient_id: recipientId,
      message: message
    },
    getAuthHeaders(token)
  ).then(r => r.data);
}

// ============================================================================
// SOCIAL FEATURES - FRIENDS' ACTIVITIES
// ============================================================================
export async function getFriendsProductActivities(token, productIds = null) {
  let url = `${API_BASE}/social/friends-activities/`;
  if (productIds && productIds.length > 0) {
    url += `?product_ids=${productIds.join(',')}`;
  }
  return axios.get(url, getAuthHeaders(token)).then(r => r.data);
}

// ============================================================================
// ALLERGY MANAGEMENT
// ============================================================================
export async function checkProductAllergies(token, productId) {
  return axios.get(`${API_BASE}/allergies/check/${productId}/`, getAuthHeaders(token)).then(r => r.data);
}

export async function checkCartAllergies(token, productIds) {
  return axios.post(
    `${API_BASE}/allergies/check-cart/`,
    { product_ids: productIds },
    getAuthHeaders(token)
  ).then(r => r.data);
}

export async function updateUserAllergies(token, allergies) {
  return axios.put(
    `${API_BASE}/allergies/update/`,
    { allergies },
    getAuthHeaders(token)
  ).then(r => r.data);
}

// ============ Wallet API ============
export async function getWalletBalance(token) {
  // Add timestamp to prevent caching
  return axios.get(`${API_BASE}/wallet/balance/?t=${Date.now()}`, getAuthHeaders(token)).then(r => r.data);
}

export async function addMoneyToWallet(token, amount) {
  return axios.post(
    `${API_BASE}/wallet/add-money/`,
    { amount },
    getAuthHeaders(token)
  ).then(r => r.data);
}

export async function getWalletTransactions(token) {
  return axios.get(`${API_BASE}/wallet/transactions/`, getAuthHeaders(token)).then(r => r.data);
}

export async function createOrderWithWallet(token, total, useWallet = false) {
  return axios.post(
    `${API_BASE}/wallet/pay-order/`,
    { total, use_wallet: useWallet },
    getAuthHeaders(token)
  ).then(r => r.data);
}

// ========== PAYMENT & ORDERS ==========
// Create payment order (supports Cashfree, Wallet, COD)
export async function createPaymentOrder(token, paymentMethod, shippingAddressId, billingAddressId, returnUrl) {
  return axios.post(
    `${API_BASE}/payment/create-order/`,
    {
      payment_method: paymentMethod,
      shipping_address_id: shippingAddressId,
      billing_address_id: billingAddressId,
      return_url: returnUrl
    },
    getAuthHeaders(token)
  ).then(r => r.data);
}

// Verify payment status
export async function verifyPayment(token, orderNumber) {
  return axios.post(
    `${API_BASE}/payment/verify/`,
    { order_number: orderNumber },
    getAuthHeaders(token)
  ).then(r => r.data);
}

// Get user's orders
export async function getUserOrders(token) {
  return axios.get(`${API_BASE}/orders/my-orders/`, getAuthHeaders(token)).then(r => r.data);
}

// Get specific order details
export async function getOrderDetail(token, orderId) {
  return axios.get(`${API_BASE}/orders/${orderId}/`, getAuthHeaders(token)).then(r => r.data);
}

// Load Cashfree SDK
export function loadCashfreeSDK() {
  return new Promise((resolve, reject) => {
    // Check if already loaded and initialized
    if (window.cashfree && typeof window.cashfree.checkout === 'function') {
      resolve(window.cashfree);
      return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://sdk.cashfree.com/js/v3/cashfree.js';
    script.async = true;
    script.onload = () => {
      // Initialize Cashfree with sandbox environment
      if (window.Cashfree) {
        window.cashfree = window.Cashfree({
          mode: "sandbox" // Use "production" for live
        });
        resolve(window.cashfree);
      } else {
        reject(new Error('Cashfree SDK failed to load'));
      }
    };
    script.onerror = () => reject(new Error('Failed to load Cashfree SDK'));
    document.body.appendChild(script);
  });
}

// Get friends who purchased a product
export async function getFriendsPurchased(productId, token) {
  return axios.get(`${API_BASE}/products/${productId}/friends-purchased/`, getAuthHeaders(token)).then(r => r.data);
}
