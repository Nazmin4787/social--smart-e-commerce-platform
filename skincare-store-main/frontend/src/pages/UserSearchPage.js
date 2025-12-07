import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { searchUsers } from '../api/socialApi';
import FollowButton from '../components/FollowButton';

const UserSearchPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

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

      {!loading && results.length > 0 && (
        <div className="users-list">
          {results.map(user => (
            <div key={user.id} className="user-item">
              <div className="user-item-left" onClick={() => navigate(`/users/${user.id}/profile`)}>
                <i className="fas fa-user-circle user-avatar"></i>
                <div className="user-item-info">
                  <h4>{user.name}</h4>
                  <p>{user.email}</p>
                  {user.bio && <p className="user-bio">{user.bio}</p>}
                  <p className="user-stats">
                    {user.followers_count} followers · {user.following_count} following
                    {user.mutual_followers_count > 0 && (
                      <> · {user.mutual_followers_count} mutual</>
                    )}
                  </p>
                </div>
              </div>
              <FollowButton
                userId={user.id}
                initialIsFollowing={user.is_following}
              />
            </div>
          ))}
        </div>
      )}

      {!loading && !searched && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-search" style={{ fontSize: '48px', color: '#ccc' }}></i>
          <p style={{ marginTop: '20px', color: '#999' }}>
            Type at least 2 characters to search for users
          </p>
        </div>
      )}
    </div>
  );
};

export default UserSearchPage;
