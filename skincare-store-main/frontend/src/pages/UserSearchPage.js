import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { searchUsers, getSuggestedUsers, getFollowers, getFollowing } from '../api/socialApi';
import FollowButton from '../components/FollowButton';

const UserSearchPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('suggested');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [suggestedUsers, setSuggestedUsers] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    console.log('User context:', user);
    if (user) {
      console.log('Fetching suggested users...');
      fetchSuggestedUsers();
      if (user.id) {
        fetchFollowers();
        fetchFollowing();
      }
    } else {
      console.log('No user logged in');
    }
  }, [user]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (query.length >= 2) {
        performSearch();
      } else {
        setResults([]);
        setSearched(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const fetchSuggestedUsers = async () => {
    const token = localStorage.getItem('access_token');
    console.log('Token for suggested users:', token ? 'exists' : 'missing');
    if (!token) {
      console.log('No token, returning early');
      return;
    }

    setLoading(true);
    try {
      console.log('Calling getSuggestedUsers API...');
      const data = await getSuggestedUsers(token);
      console.log('Suggested users data received:', data);
      console.log('Number of suggested users:', data.suggested_users?.length || 0);
      setSuggestedUsers(data.suggested_users || []);
    } catch (error) {
      console.error('Error fetching suggested users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFollowers = async () => {
    const token = localStorage.getItem('access_token');
    if (!token || !user?.id) return;

    try {
      const data = await getFollowers(user.id, 1, token);
      setFollowers(data.followers || []);
    } catch (error) {
      console.error('Error fetching followers:', error);
    }
  };

  const fetchFollowing = async () => {
    const token = localStorage.getItem('access_token');
    if (!token || !user?.id) return;

    try {
      const data = await getFollowing(user.id, 1, token);
      setFollowing(data.following || []);
    } catch (error) {
      console.error('Error fetching following:', error);
    }
  };

  const performSearch = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const data = await searchUsers(query, 1, token);
      setResults(data.users);
      setSearched(true);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Show message for admin users
  if (user && (user.is_staff || user.is_superuser)) {
    return (
      <div className="user-search-page">
        <div className="user-search-container">
          <div className="user-search-header">
            <h1>Search Users</h1>
          </div>
          <div className="search-info" style={{ padding: '3rem', textAlign: 'center', background: 'white', borderRadius: '12px' }}>
            <i className="fas fa-user-shield" style={{ fontSize: '4rem', color: '#e53e3e', marginBottom: '1rem' }}></i>
            <h3 style={{ color: '#2d3748', marginBottom: '0.5rem' }}>Admin Access Only</h3>
            <p style={{ color: '#718096' }}>Social features like following users are only available to regular users. As an admin, you can manage users through the Admin Panel.</p>
            <button 
              onClick={() => navigate('/')} 
              style={{ marginTop: '1.5rem', padding: '0.75rem 1.5rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  const getUserList = () => {
    if (query.length >= 2) {
      return results;
    }
    switch (activeTab) {
      case 'suggested':
        return suggestedUsers;
      case 'followers':
        return followers;
      case 'following':
        return following;
      default:
        return [];
    }
  };

  const currentUsers = getUserList();

  return (
    <div className="container" style={{ padding: '40px 20px' }}>
      <div className="search-header">
        <h2>
          <i className="fas fa-search"></i> Search Users
        </h2>
        <div className="search-input-container">
          <i className="fas fa-search search-icon"></i>
          <input
            type="text"
            className="search-input"
            placeholder="Search by name or email..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          {query && (
            <button className="clear-search" onClick={() => setQuery('')}>
              <i className="fas fa-times"></i>
            </button>
          )}
        </div>
      </div>

      {!query && (
        <div className="user-tabs">
          <button
            className={`user-tab ${activeTab === 'suggested' ? 'active' : ''}`}
            onClick={() => setActiveTab('suggested')}
          >
            <i className="fas fa-user-plus"></i> Suggested
          </button>
          <button
            className={`user-tab ${activeTab === 'followers' ? 'active' : ''}`}
            onClick={() => setActiveTab('followers')}
          >
            <i className="fas fa-user-friends"></i> Followers
          </button>
          <button
            className={`user-tab ${activeTab === 'following' ? 'active' : ''}`}
            onClick={() => setActiveTab('following')}
          >
            <i className="fas fa-user-check"></i> Following
          </button>
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-spinner fa-spin" style={{ fontSize: '32px' }}></i>
          <p style={{ marginTop: '10px' }}>Searching...</p>
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-user-slash" style={{ fontSize: '48px', color: '#ccc' }}></i>
          <p style={{ marginTop: '20px', color: '#999' }}>No users found for "{query}"</p>
        </div>
      )}

      {!loading && currentUsers.length > 0 && (
        <div className="users-list">
          {currentUsers.map(userItem => (
            <div key={userItem.id} className="user-item">
              <div className="user-item-left" onClick={() => navigate(`/users/${userItem.id}/profile`)}>
                <i className="fas fa-user-circle user-avatar"></i>
                <div className="user-item-info">
                  <h4>{userItem.name}</h4>
                  <p>{userItem.email}</p>
                  {userItem.bio && <p className="user-bio">{userItem.bio}</p>}
                  <p className="user-stats">
                    {userItem.followers_count} followers · {userItem.following_count || 0} following
                    {userItem.mutual_followers_count > 0 && (
                      <> · {userItem.mutual_followers_count} mutual</>
                    )}
                  </p>
                </div>
              </div>
              <FollowButton
                userId={userItem.id}
                initialIsFollowing={userItem.is_following}
              />
            </div>
          ))}
        </div>
      )}

      {!loading && !query && currentUsers.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-users" style={{ fontSize: '48px', color: '#ccc' }}></i>
          <p style={{ marginTop: '20px', color: '#999' }}>
            {activeTab === 'suggested' && 'No suggestions available at the moment'}
            {activeTab === 'followers' && 'No followers yet'}
            {activeTab === 'following' && 'Not following anyone yet'}
          </p>
        </div>
      )}
    </div>
  );
};

export default UserSearchPage;
