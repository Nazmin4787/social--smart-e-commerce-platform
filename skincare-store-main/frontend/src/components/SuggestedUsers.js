import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSuggestedUsers } from '../api/socialApi';
import { AuthContext } from '../context/AuthContext';
import FollowButton from './FollowButton';

const SuggestedUsers = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchSuggestedUsers();
    }
  }, [user]);

  const fetchSuggestedUsers = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const data = await getSuggestedUsers(token);
      setUsers(data.suggested_users.slice(0, 5)); // Show only 5
    } catch (error) {
      console.error('Error fetching suggested users:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user || loading || users.length === 0) return null;

  return (
    <section className="suggested-users-section">
      <div className="container">
        <div className="section-header">
          <h3>
            <i className="fas fa-user-friends"></i> Suggested Users
          </h3>
          <button className="btn-see-all" onClick={() => navigate('/search/users')}>
            See All
          </button>
        </div>
        
        <div className="suggested-users-grid">
          {users.map(suggestedUser => (
            <div key={suggestedUser.id} className="suggested-user-card">
              <div className="suggested-user-header" onClick={() => navigate(`/users/${suggestedUser.id}/profile`)}>
                <i className="fas fa-user-circle suggested-user-avatar"></i>
                <h4>{suggestedUser.name}</h4>
                <p className="suggested-user-email">{suggestedUser.email}</p>
                <p className="suggested-user-stats">
                  {suggestedUser.followers_count} followers
                </p>
              </div>
              <FollowButton
                userId={suggestedUser.id}
                initialIsFollowing={suggestedUser.is_following}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SuggestedUsers;
