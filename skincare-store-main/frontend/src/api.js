import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

// Helper function to get auth headers
const getAuthHeaders = (token) => ({
  headers: { 'Authorization': `Bearer ${token}` }
});

// Products
export async function fetchProducts() {
  return axios.get(`${API_BASE}/products/`).then(r => r.data);
}

// Authentication
export async function register(name, email, password) {
  return axios.post(`${API_BASE}/auth/register/`, { name, email, password }).then(r => r.data);
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

// Orders
export async function createOrder(token, items, total) {
  return axios.post(
    `${API_BASE}/orders/create/`,
    { items, total },
    getAuthHeaders(token)
  ).then(r => r.data);
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
