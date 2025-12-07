import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { searchUsers, getSuggestedUsers, getFollowers, getFollowing } from '../api/socialApi';
import { getOrCreateConversation } from '../api/chatApi';
import Header from '../components/Header';
import FollowButton from '../components/FollowButton';

const SocialPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [suggestedUsers, setSuggestedUsers] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }

    // Show admin restriction message
    if (user.is_staff && user.is_superuser) {
      return;
    }

    // Load data based on active tab
    if (activeTab === 'suggested') {
      fetchSuggestedUsers();
    } else if (activeTab === 'followers') {
      fetchFollowers();
    } else if (activeTab === 'following') {
      fetchFollowing();
    }
  }, [activeTab, user, navigate]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchQuery.length >= 2 && activeTab === 'search') {
        performSearch();
      } else if (searchQuery.length === 0) {
        setSearchResults([]);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, activeTab]);

  const performSearch = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const data = await searchUsers(searchQuery, 1, token);
      setSearchResults(data.users);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSuggestedUsers = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      console.log('Fetching suggested users...');
      const data = await getSuggestedUsers(token);
      console.log('Suggested users response:', data);
      setSuggestedUsers(data.suggested_users || []);
    } catch (error) {
      console.error('Error fetching suggested users:', error);
      setSuggestedUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchFollowers = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const data = await getFollowers(user.id, 1, token);
      setFollowers(data.followers);
    } catch (error) {
      console.error('Error fetching followers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFollowing = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const data = await getFollowing(user.id, 1, token);
      setFollowing(data.following);
    } catch (error) {
      console.error('Error fetching following:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFollowChange = (isFollowing) => {
    // Refresh the current tab data
    if (activeTab === 'suggested') {
      fetchSuggestedUsers();
    } else if (activeTab === 'followers') {
      fetchFollowers();
    } else if (activeTab === 'following') {
      fetchFollowing();
    }
  };

  const handleStartChat = async (otherUserId) => {
    const token = localStorage.getItem('access_token');

    try {
      const data = await getOrCreateConversation(otherUserId, token);
      navigate(`/messages/${data.conversation.id}`);
    } catch (error) {
      console.error('Error creating conversation:', error);
      alert(error.error || 'You can only chat with mutual friends');
    }
  };

  // Show message for admin users
  if (user && (user.is_staff && user.is_superuser)) {
    return (
      <>
        <Header />
        <div className="social-page">
          <div className="social-page-container">
            <div className="admin-restriction-message">
              <i className="fas fa-user-shield"></i>
              <h2>Admin Access Only</h2>
              <p>Social features are only available to regular users. As an admin, you can manage users through the Admin Panel.</p>
              <button className="btn-primary" onClick={() => navigate('/')}>
                Go to Home
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="social-page">
        <div className="social-page-container">
          <div className="social-page-header">
            <h1>
              <i className="fas fa-users"></i> Social
            </h1>
            <p>Connect with other users, discover new people, and manage your connections</p>
          </div>

          {/* Tabs */}
          <div className="social-tabs">
            <button
              className={`social-tab ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              <i className="fas fa-search"></i> Search Users
            </button>
            <button
              className={`social-tab ${activeTab === 'suggested' ? 'active' : ''}`}
              onClick={() => setActiveTab('suggested')}
            >
              <i className="fas fa-user-plus"></i> Suggested
            </button>
            <button
              className={`social-tab ${activeTab === 'followers' ? 'active' : ''}`}
              onClick={() => setActiveTab('followers')}
            >
              <i className="fas fa-user-friends"></i> Followers
            </button>
            <button
              className={`social-tab ${activeTab === 'following' ? 'active' : ''}`}
              onClick={() => setActiveTab('following')}
            >
              <i className="fas fa-user-check"></i> Following
            </button>
          </div>

          {/* Search Tab */}
          {activeTab === 'search' && (
            <div className="social-tab-content">
              <div className="search-box">
                <i className="fas fa-search"></i>
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
                {searchQuery && (
                  <button className="clear-btn" onClick={() => setSearchQuery('')}>
                    <i className="fas fa-times"></i>
                  </button>
                )}
              </div>

              {loading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Searching...</p>
                </div>
              ) : searchResults && searchResults.length > 0 ? (
                <div className="users-grid">
                  {searchResults.map((searchUser) => (
                    <div key={searchUser.id} className="user-card">
                      <div className="user-card-avatar" onClick={() => navigate(`/users/${searchUser.id}/profile`)}>
                        <i className="fas fa-user-circle"></i>
                      </div>
                      <div className="user-card-info">
                        <h3 onClick={() => navigate(`/users/${searchUser.id}/profile`)}>{searchUser.name}</h3>
                        <p>{searchUser.email}</p>
                        <div className="user-card-stats">
                          <span>{searchUser.followers_count} followers</span>
                          <span>•</span>
                          <span>{searchUser.following_count} following</span>
                        </div>
                      </div>
                      <FollowButton
                        userId={searchUser.id}
                        initialIsFollowing={searchUser.is_following}
                        onFollowChange={handleFollowChange}
                      />
                    </div>
                  ))}
                </div>
              ) : searchQuery.length >= 2 ? (
                <div className="empty-state">
                  <i className="fas fa-user-slash"></i>
                  <p>No users found matching "{searchQuery}"</p>
                </div>
              ) : (
                <div className="empty-state">
                  <i className="fas fa-search"></i>
                  <p>Start typing to search for users</p>
                </div>
              )}
            </div>
          )}

          {/* Suggested Tab */}
          {activeTab === 'suggested' && (
            <div className="social-tab-content">
              {loading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Loading suggestions...</p>
                </div>
              ) : suggestedUsers && suggestedUsers.length > 0 ? (
                <div className="users-grid">
                  {suggestedUsers.map((suggestedUser) => (
                    <div key={suggestedUser.id} className="user-card">
                      <div className="user-card-avatar" onClick={() => navigate(`/users/${suggestedUser.id}/profile`)}>
                        <i className="fas fa-user-circle"></i>
                      </div>
                      <div className="user-card-info">
                        <h3 onClick={() => navigate(`/users/${suggestedUser.id}/profile`)}>{suggestedUser.name}</h3>
                        <p>{suggestedUser.email}</p>
                        <div className="user-card-stats">
                          <span>{suggestedUser.followers_count} followers</span>
                          <span>•</span>
                          <span>{suggestedUser.following_count} following</span>
                        </div>
                      </div>
                      <FollowButton
                        userId={suggestedUser.id}
                        initialIsFollowing={false}
                        onFollowChange={handleFollowChange}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="fas fa-users"></i>
                  <p>No suggestions available at the moment</p>
                </div>
              )}
            </div>
          )}

          {/* Followers Tab */}
          {activeTab === 'followers' && (
            <div className="social-tab-content">
              {loading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Loading followers...</p>
                </div>
              ) : followers && followers.length > 0 ? (
                <div className="users-grid">
                  {followers.map((follower) => (
                    <div key={follower.id} className="user-card">
                      <div className="user-card-avatar" onClick={() => navigate(`/users/${follower.id}/profile`)}>
                        <i className="fas fa-user-circle"></i>
                      </div>
                      <div className="user-card-info">
                        <h3 onClick={() => navigate(`/users/${follower.id}/profile`)}>{follower.name}</h3>
                        <p>{follower.email}</p>
                        <div className="user-card-stats">
                          <span>{follower.followers_count} followers</span>
                          <span>•</span>
                          <span>{follower.following_count} following</span>
                        </div>
                      </div>
                      <div className="user-card-actions">
                        {follower.is_following && (
                          <button 
                            className="chat-btn" 
                            onClick={() => handleStartChat(follower.id)}
                            title="Send Message"
                          >
                            <i className="fas fa-comment-dots"></i>
                          </button>
                        )}
                        <FollowButton
                          userId={follower.id}
                          initialIsFollowing={follower.is_following}
                          onFollowChange={handleFollowChange}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="fas fa-user-slash"></i>
                  <p>You don't have any followers yet</p>
                </div>
              )}
            </div>
          )}

          {/* Following Tab */}
          {activeTab === 'following' && (
            <div className="social-tab-content">
              {loading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Loading following...</p>
                </div>
              ) : following && following.length > 0 ? (
                <div className="users-grid">
                  {following.map((followedUser) => (
                    <div key={followedUser.id} className="user-card">
                      <div className="user-card-avatar" onClick={() => navigate(`/users/${followedUser.id}/profile`)}>
                        <i className="fas fa-user-circle"></i>
                      </div>
                      <div className="user-card-info">
                        <h3 onClick={() => navigate(`/users/${followedUser.id}/profile`)}>{followedUser.name}</h3>
                        <p>{followedUser.email}</p>
                        <div className="user-card-stats">
                          <span>{followedUser.followers_count} followers</span>
                          <span>•</span>
                          <span>{followedUser.following_count} following</span>
                        </div>
                      </div>
                      <div className="user-card-actions">
                        {followedUser.is_following && (
                          <button 
                            className="chat-btn" 
                            onClick={() => handleStartChat(followedUser.id)}
                            title="Send Message"
                          >
                            <i className="fas fa-comment-dots"></i>
                          </button>
                        )}
                        <FollowButton
                          userId={followedUser.id}
                          initialIsFollowing={true}
                          onFollowChange={handleFollowChange}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="fas fa-user-times"></i>
                  <p>You're not following anyone yet</p>
                  <button className="btn-primary" onClick={() => setActiveTab('suggested')}>
                    Discover Users
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default SocialPage;
