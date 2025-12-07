import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { getProfile, getLikedProducts, likeProduct, addToCart, updateUserAllergies } from '../api';
import { getUserProfile, getFollowers, getFollowing } from '../api/socialApi';
import Header from '../components/Header';
import ProductCard from '../components/ProductCard';
import AllergySelector from '../components/AllergySelector';

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
  const [isEditingAllergies, setIsEditingAllergies] = useState(false);
  const [allergies, setAllergies] = useState([]);
  const [savingAllergies, setSavingAllergies] = useState(false);
  const [socialStats, setSocialStats] = useState(null);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [socialLoading, setSocialLoading] = useState(false);
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
    } else if (activeTab === 'social') {
      fetchSocialData();
    }
  }, [user, navigate, activeTab]);

  const fetchProfile = async () => {
    try {
      const data = await getProfile(user.token);
      setProfile(data);
      setAllergies(data.allergies || []);
      // Fetch social stats
      const socialData = await getUserProfile(user.token, user.id);
      setSocialStats(socialData);
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

  const fetchSocialData = async () => {
    setSocialLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const [followersData, followingData] = await Promise.all([
        getFollowers(user.id, 1, token),
        getFollowing(user.id, 1, token)
      ]);
      setFollowers(followersData.followers);
      setFollowing(followingData.following);
    } catch (error) {
      console.error('Error fetching social data:', error);
    } finally {
      setSocialLoading(false);
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

  const handleEditAllergiesClick = () => {
    setIsEditingAllergies(true);
  };

  const handleCancelAllergyEdit = () => {
    setIsEditingAllergies(false);
    setAllergies(profile.allergies || []);
  };

  const handleSaveAllergies = async () => {
    setSavingAllergies(true);
    try {
      const token = localStorage.getItem('accessToken');
      await updateUserAllergies(token, allergies);
      alert('Allergies updated successfully!');
      setIsEditingAllergies(false);
      // Refresh profile to get updated data
      await fetchProfile();
    } catch (error) {
      console.error('Error updating allergies:', error);
      alert(error.response?.data?.error || 'Failed to update allergies');
    } finally {
      setSavingAllergies(false);
    }
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
              {socialStats && (
                <div className="profile-social-stats">
                  <div 
                    className="stat-item" 
                    onClick={() => navigate(`/users/${user.id}/followers`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="stat-number">{socialStats.followers_count}</div>
                    <div className="stat-label">Followers</div>
                  </div>
                  <div 
                    className="stat-item" 
                    onClick={() => navigate(`/users/${user.id}/following`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="stat-number">{socialStats.following_count}</div>
                    <div className="stat-label">Following</div>
                  </div>
                </div>
              )}
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
                className={`profile-nav-item ${activeTab === 'track' ? 'active' : ''}`}
                onClick={() => navigate('/orders')}
              >
                <i className="fas fa-truck"></i>
                <span>Track Orders</span>
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
                className={`profile-nav-item ${activeTab === 'allergies' ? 'active' : ''}`}
                onClick={() => setActiveTab('allergies')}
              >
                <i className="fas fa-exclamation-triangle"></i>
                <span>My Allergies</span>
              </button>
              {user && !user.is_staff && !user.is_superuser && (
                <button 
                  className={`profile-nav-item ${activeTab === 'social' ? 'active' : ''}`}
                  onClick={() => setActiveTab('social')}
                >
                  <i className="fas fa-users"></i>
                  <span>Followers & Following</span>
                </button>
              )}
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

            {activeTab === 'allergies' && (
              <div className="profile-section">
                <h2 className="section-heading">
                  <i className="fas fa-exclamation-triangle"></i> My Allergies
                </h2>
                
                {!isEditingAllergies ? (
                  <div className="allergies-view">
                    <div className="allergies-header">
                      <p className="allergies-description">
                        Manage your skin allergies to help us recommend safe products for you.
                      </p>
                      <button 
                        className="edit-allergies-btn"
                        onClick={handleEditAllergiesClick}
                      >
                        <i className="fas fa-edit"></i> Edit Allergies
                      </button>
                    </div>
                    
                    {allergies && allergies.length > 0 ? (
                      <div className="allergies-display">
                        <h3>Your Current Allergies:</h3>
                        <div className="allergy-chips">
                          {allergies.map((allergy, index) => (
                            <span key={index} className="allergy-chip">
                              <i className="fas fa-exclamation-circle"></i>
                              {allergy}
                            </span>
                          ))}
                        </div>
                        <div className="allergy-info-box">
                          <i className="fas fa-shield-alt"></i>
                          <p>We'll alert you if products contain these ingredients and suggest safer alternatives.</p>
                        </div>
                      </div>
                    ) : (
                      <div className="no-allergies">
                        <i className="fas fa-check-circle"></i>
                        <p>You haven't added any allergies yet.</p>
                        <p className="no-allergies-sub">Click "Edit Allergies" to add ingredients you want to avoid.</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="allergies-edit">
                    <p className="edit-instructions">
                      Select all ingredients that cause allergic reactions for you:
                    </p>
                    <AllergySelector 
                      selectedAllergies={allergies}
                      onChange={setAllergies}
                    />
                    <div className="allergy-edit-actions">
                      <button 
                        className="save-allergies-btn"
                        onClick={handleSaveAllergies}
                        disabled={savingAllergies}
                      >
                        {savingAllergies ? (
                          <>
                            <div className="button-spinner"></div>
                            Saving...
                          </>
                        ) : (
                          <>
                            <i className="fas fa-save"></i> Save Changes
                          </>
                        )}
                      </button>
                      <button 
                        className="cancel-allergies-btn"
                        onClick={handleCancelAllergyEdit}
                        disabled={savingAllergies}
                      >
                        <i className="fas fa-times"></i> Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'social' && (
              <div className="profile-section">
                <h2 className="section-heading">Followers & Following</h2>
                {socialLoading ? (
                  <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>Loading...</p>
                  </div>
                ) : (
                  <div className="social-section-content">
                    {/* Followers Section */}
                    <div className="social-card">
                      <div className="social-card-header">
                        <h3>
                          <i className="fas fa-user-friends"></i> Followers
                          <span className="count-badge">{socialStats?.followers_count || 0}</span>
                        </h3>
                        {followers.length > 0 && (
                          <button 
                            className="view-all-btn" 
                            onClick={() => navigate(`/users/${user.id}/followers`)}
                          >
                            View All <i className="fas fa-arrow-right"></i>
                          </button>
                        )}
                      </div>
                      <div className="social-users-list">
                        {followers.length === 0 ? (
                          <div className="empty-state">
                            <i className="fas fa-user-slash"></i>
                            <p>No followers yet</p>
                          </div>
                        ) : (
                          followers.slice(0, 5).map((follower) => (
                            <div 
                              key={follower.id} 
                              className="social-user-item"
                              onClick={() => navigate(`/users/${follower.id}/profile`)}
                            >
                              <div className="social-user-avatar">
                                <i className="fas fa-user-circle"></i>
                              </div>
                              <div className="social-user-info">
                                <h4>{follower.name}</h4>
                                <p>{follower.email}</p>
                              </div>
                              <i className="fas fa-chevron-right"></i>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Following Section */}
                    <div className="social-card">
                      <div className="social-card-header">
                        <h3>
                          <i className="fas fa-user-check"></i> Following
                          <span className="count-badge">{socialStats?.following_count || 0}</span>
                        </h3>
                        {following.length > 0 && (
                          <button 
                            className="view-all-btn" 
                            onClick={() => navigate(`/users/${user.id}/following`)}
                          >
                            View All <i className="fas fa-arrow-right"></i>
                          </button>
                        )}
                      </div>
                      <div className="social-users-list">
                        {following.length === 0 ? (
                          <div className="empty-state">
                            <i className="fas fa-user-times"></i>
                            <p>Not following anyone yet</p>
                            <button 
                              className="btn-primary" 
                              onClick={() => navigate('/search/users')}
                              style={{ marginTop: '1rem', padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                            >
                              Find Users
                            </button>
                          </div>
                        ) : (
                          following.slice(0, 5).map((followedUser) => (
                            <div 
                              key={followedUser.id} 
                              className="social-user-item"
                              onClick={() => navigate(`/users/${followedUser.id}/profile`)}
                            >
                              <div className="social-user-avatar">
                                <i className="fas fa-user-circle"></i>
                              </div>
                              <div className="social-user-info">
                                <h4>{followedUser.name}</h4>
                                <p>{followedUser.email}</p>
                              </div>
                              <i className="fas fa-chevron-right"></i>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
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