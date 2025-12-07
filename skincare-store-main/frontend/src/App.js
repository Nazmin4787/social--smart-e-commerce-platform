import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import ProductDetailPage from './pages/ProductDetailPage';
import CartPage from './pages/CartPage';
import BookingPage from './pages/BookingPage';
import AdminDashboard from './pages/AdminDashboard';
import OrdersPage from './pages/OrdersPage';
import UserProfilePage from './pages/UserProfilePage';
import FollowersPage from './pages/FollowersPage';
import FollowingPage from './pages/FollowingPage';
import UserSearchPage from './pages/UserSearchPage';
import NotificationsPage from './pages/NotificationsPage';
import SocialPage from './pages/SocialPage';
import MessagesPage from './pages/MessagesPage';
import './styles.css';

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <Router>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/products/:id" element={<ProductDetailPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/book/:id" element={<BookingPage />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/social" element={<SocialPage />} />
            <Route path="/messages" element={<MessagesPage />} />
            <Route path="/messages/:conversationId" element={<MessagesPage />} />
            <Route path="/users/:userId/profile" element={<UserProfilePage />} />
            <Route path="/users/:userId/followers" element={<FollowersPage />} />
            <Route path="/users/:userId/following" element={<FollowingPage />} />
            <Route path="/search/users" element={<UserSearchPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
          </Routes>
        </Router>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
