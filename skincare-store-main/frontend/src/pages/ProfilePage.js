import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { getProfile, getLikedProducts, likeProduct, addToCart } from '../api';
import Header from '../components/Header';
import ProductCard from '../components/ProductCard';

const ProfilePage = () => {
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile');
  const [likedProducts, setLikedProducts] = useState([]);
  const [likedProductsLoading, setLikedProductsLoading] = useState(false);
  const [likedProductIds, setLikedProductIds] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    email: '',
    phone: '',
    bio: ''
  });

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    fetchProfile();
    if (activeTab === 'liked') {
      fetchLikedProducts();
    }
  }, [user, navigate, activeTab]);

  const fetchProfile = async () => {
    try {
      const data = await getProfile(user.token);
      setProfile(data);
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLikedProducts = async () => {
    setLikedProductsLoading(true);
    try {
      const data = await getLikedProducts(user.token);
      console.log('Fetched liked products:', data);
      setLikedProducts(data);
      setLikedProductIds(data.map(item => item.product.id));
    } catch (error) {
      console.error('Error fetching liked products:', error);
      setLikedProducts([]);
    } finally {
      setLikedProductsLoading(false);
    }
  };

  const handleLike = async (productId) => {
    try {
      await likeProduct(user.token, productId);
      // Refresh liked products
      fetchLikedProducts();
    } catch (error) {
      console.error('Error toggling like:', error);
      alert('Failed to update like status');
    }
  };

  const handleAddToCart = async (product) => {
    try {
      await addToCart(user.token, product.id, 1);
      alert('Product added to cart!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert(error.response?.data?.error || 'Failed to add to cart');
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleEditClick = () => {
    setEditForm({
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      bio: profile.bio || ''
    });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditForm({ name: '', email: '', phone: '', bio: '' });
  };

  const handleSaveChanges = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('http://localhost:8000/api/profile/update/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(editForm)
      });

      if (response.ok) {
        const updatedProfile = await response.json();
        setProfile(updatedProfile);
        setIsEditing(false);
        alert('Profile updated successfully!');
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile');
    }
  };

  const handleFormChange = (e) => {
    setEditForm({
      ...editForm,
      [e.target.name]: e.target.value
    });
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className="profile-loading">
          <div className="spinner"></div>
          <p>Loading profile...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="profile-page">
        <div className="profile-container">
          {/* Sidebar */}
          <aside className="profile-sidebar">
            <div className="profile-user-info">
              <div className="profile-avatar">
                <i className="fas fa-user-circle"></i>
              </div>
              <h3>{profile?.name}</h3>
              <p>{profile?.email}</p>
            </div>

            <nav className="profile-nav">
              <button 
                className={`profile-nav-item ${activeTab === 'profile' ? 'active' : ''}`}
                onClick={() => setActiveTab('profile')}
              >
                <i className="fas fa-user"></i>
                <span>My Profile</span>
              </button>
              <button 
                className={`profile-nav-item ${activeTab === 'orders' ? 'active' : ''}`}
                onClick={() => setActiveTab('orders')}
              >
                <i className="fas fa-box"></i>
                <span>My Orders</span>
              </button>
              <button 
                className={`profile-nav-item ${activeTab === 'addresses' ? 'active' : ''}`}
                onClick={() => setActiveTab('addresses')}
              >
                <i className="fas fa-map-marker-alt"></i>
                <span>Addresses</span>
              </button>
              <button 
                className={`profile-nav-item ${activeTab === 'liked' ? 'active' : ''}`}
                onClick={() => setActiveTab('liked')}
              >
                <i className="fas fa-heart"></i>
                <span>Liked Products</span>
              </button>
              <button 
                className={`profile-nav-item ${activeTab === 'password' ? 'active' : ''}`}
                onClick={() => setActiveTab('password')}
              >
                <i className="fas fa-lock"></i>
                <span>Change Password</span>
              </button>
              <button 
                className="profile-nav-item logout-btn"
                onClick={handleLogout}
              >
                <i className="fas fa-sign-out-alt"></i>
                <span>Logout</span>
              </button>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="profile-main">
            {activeTab === 'profile' && (
              <div className="profile-section">
                <h2 className="section-heading">My Profile</h2>
                {isEditing ? (
                  <div className="profile-edit-card">
                    <div className="form-field">
                      <label>Full Name</label>
                      <input 
                        type="text" 
                        name="name" 
                        value={editForm.name} 
                        onChange={handleFormChange}
                        placeholder="Enter your full name"
                      />
                    </div>
                    <div className="form-field">
                      <label>Email Address</label>
                      <input 
                        type="email" 
                        name="email" 
                        value={editForm.email} 
                        onChange={handleFormChange}
                        placeholder="Enter your email"
                      />
                    </div>
                    <div className="form-field">
                      <label>Bio</label>
                      <textarea 
                        name="bio" 
                        value={editForm.bio} 
                        onChange={handleFormChange}
                        rows="4"
                        placeholder="Tell us about yourself..."
                      />
                    </div>
                    <div className="form-field">
                      <label>Phone Number</label>
                      <input 
                        type="tel" 
                        name="phone" 
                        value={editForm.phone} 
                        onChange={handleFormChange}
                        placeholder="Enter your phone number"
                      />
                    </div>
                    <div className="profile-actions">
                      <button className="btn-primary" onClick={handleSaveChanges}>Save Changes</button>
                      <button className="btn-secondary" onClick={handleCancelEdit}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="profile-details-card">
                    <div className="profile-detail-row">
                      <label>Full Name</label>
                      <span>{profile?.name || 'N/A'}</span>
                    </div>
                    <div className="profile-detail-row">
                      <label>Email Address</label>
                      <span>{profile?.email || 'N/A'}</span>
                    </div>
                    {profile?.bio && (
                      <div className="profile-detail-row">
                        <label>Bio</label>
                        <span>{profile.bio}</span>
                      </div>
                    )}
                    <div className="profile-detail-row">
                      <label>Phone Number</label>
                      <span>{profile?.phone || 'Not provided'}</span>
                    </div>
                    <div className="profile-detail-row">
                      <label>Member Since</label>
                      <span>{profile?.date_joined ? new Date(profile.date_joined).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'}</span>
                    </div>
                    <div className="profile-actions">
                      <button className="btn-primary" onClick={handleEditClick}>Edit Profile</button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'orders' && (
              <div className="profile-section">
                <h2 className="section-heading">My Orders</h2>
                <div className="orders-empty">
                  <i className="fas fa-shopping-bag"></i>
                  <p>You haven't placed any orders yet</p>
                  <button className="btn-primary" onClick={() => navigate('/')}>
                    Start Shopping
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'addresses' && (
              <div className="profile-section">
                <h2 className="section-heading">Saved Addresses</h2>
                <div className="addresses-empty">
                  <i className="fas fa-map-marker-alt"></i>
                  <p>No saved addresses</p>
                  <button className="btn-primary">Add New Address</button>
                </div>
              </div>
            )}

            {activeTab === 'liked' && (
              <div className="profile-section">
                <h2 className="section-heading">Liked Products</h2>
                {likedProductsLoading ? (
                  <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>Loading liked products...</p>
                  </div>
                ) : likedProducts.length === 0 ? (
                  <div className="liked-empty">
                    <i className="fas fa-heart"></i>
                    <p>You haven't liked any products yet</p>
                    <button className="btn-primary" onClick={() => navigate('/')}>
                      Explore Products
                    </button>
                  </div>
                ) : (
                  <div className="products-grid">
                    {likedProducts.map((item) => (
                      <ProductCard
                        key={item.product.id}
                        product={item.product}
                        onLike={handleLike}
                        onAddToCart={handleAddToCart}
                        isLiked={true}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'password' && (
              <div className="profile-section">
                <h2 className="section-heading">Change Password</h2>
                <form className="password-form">
                  <div className="form-field">
                    <label>Current Password</label>
                    <input type="password" placeholder="Enter current password" />
                  </div>
                  <div className="form-field">
                    <label>New Password</label>
                    <input type="password" placeholder="Enter new password" />
                  </div>
                  <div className="form-field">
                    <label>Confirm New Password</label>
                    <input type="password" placeholder="Confirm new password" />
                  </div>
                  <button type="submit" className="btn-primary">Update Password</button>
                </form>
              </div>
            )}
          </main>
        </div>
      </div>
    </>
  );
};

export default ProfilePage;
