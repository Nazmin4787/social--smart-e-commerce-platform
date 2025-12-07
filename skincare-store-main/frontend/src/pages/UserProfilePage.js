import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getUserProfile } from '../api/socialApi';
import { AuthContext } from '../context/AuthContext';
import FollowButton from '../components/FollowButton';

const UserProfilePage = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUserProfile();
  }, [userId]);

  const fetchUserProfile = async () => {
    setLoading(true);
    setError(null);
    const token = localStorage.getItem('access_token');

    try {
      const data = await getUserProfile(userId, token);
      setProfile(data);
    } catch (err) {
      console.error('Error fetching profile:', err);
      setError('Failed to load user profile');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowChange = (isNowFollowing) => {
    setProfile(prev => ({
      ...prev,
      is_following: isNowFollowing,
      followers_count: isNowFollowing 
        ? prev.followers_count + 1 
        : prev.followers_count - 1
    }));
  };

  if (loading) {
    return (
      <div className="container" style={{ padding: '40px 20px', textAlign: 'center' }}>
        <i className="fas fa-spinner fa-spin" style={{ fontSize: '48px', color: '#d4a574' }}></i>
        <p style={{ marginTop: '20px' }}>Loading profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '40px 20px', textAlign: 'center' }}>
        <i className="fas fa-exclamation-circle" style={{ fontSize: '48px', color: '#e74c3c' }}></i>
        <p style={{ marginTop: '20px', color: '#e74c3c' }}>{error}</p>
        <button className="btn" onClick={() => navigate('/')}>Go Home</button>
      </div>
    );
  }

  if (!profile) return null;

  const isOwnProfile = user && user.id === parseInt(userId);

  return (
    <div className="user-profile-page">
      <div className="container" style={{ padding: '40px 20px' }}>
        <div className="profile-header">
          <div className="profile-avatar">
            <i className="fas fa-user-circle" style={{ fontSize: '120px', color: '#d4a574' }}></i>
          </div>
          
          <div className="profile-info">
            <div className="profile-name-section">
              <h1>{profile.name}</h1>
              {!isOwnProfile && (
                <FollowButton
                  userId={parseInt(userId)}
                  initialIsFollowing={profile.is_following}
                  onFollowChange={handleFollowChange}
                />
              )}
              {isOwnProfile && (
                <Link to="/profile" className="btn-edit-profile">
                  <i className="fas fa-edit"></i> Edit Profile
                </Link>
              )}
            </div>

            <div className="profile-stats">
              <div className="stat-item">
                <span className="stat-number">{profile.liked_products_count || 0}</span>
                <span className="stat-label">Liked Products</span>
              </div>
              <Link to={`/users/${userId}/followers`} className="stat-item clickable">
                <span className="stat-number">{profile.followers_count}</span>
                <span className="stat-label">Followers</span>
              </Link>
              <Link to={`/users/${userId}/following`} className="stat-item clickable">
                <span className="stat-number">{profile.following_count}</span>
                <span className="stat-label">Following</span>
              </Link>
            </div>

            <div className="profile-details">
              <p className="profile-email">
                <i className="fas fa-envelope"></i> {profile.email}
              </p>
              {profile.bio && (
                <p className="profile-bio">{profile.bio}</p>
              )}
              {!isOwnProfile && profile.mutual_followers_count > 0 && (
                <p className="mutual-followers">
                  <i className="fas fa-users"></i> {profile.mutual_followers_count} mutual {profile.mutual_followers_count === 1 ? 'follower' : 'followers'}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;
