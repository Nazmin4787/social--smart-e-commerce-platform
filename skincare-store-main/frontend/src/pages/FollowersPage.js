import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getFollowers } from '../api/socialApi';
import FollowButton from '../components/FollowButton';

const FollowersPage = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [followers, setFollowers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    fetchFollowers();
  }, [userId, page]);

  const fetchFollowers = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const data = await getFollowers(userId, page, token);
      setFollowers(prev => page === 1 ? data.followers : [...prev, ...data.followers]);
      setHasMore(data.has_more);
    } catch (error) {
      console.error('Error fetching followers:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: '40px 20px' }}>
      <div className="social-list-header">
        <button onClick={() => navigate(-1)} className="btn-back">
          <i className="fas fa-arrow-left"></i> Back
        </button>
        <h2>Followers</h2>
      </div>

      <div className="users-list">
        {followers.map(follower => (
          <div key={follower.id} className="user-item">
            <div className="user-item-left" onClick={() => navigate(`/users/${follower.id}/profile`)}>
              <i className="fas fa-user-circle user-avatar"></i>
              <div className="user-item-info">
                <h4>{follower.name}</h4>
                <p>{follower.email}</p>
                {follower.bio && <p className="user-bio">{follower.bio}</p>}
                <p className="user-stats">
                  {follower.followers_count} followers · {follower.following_count} following
                </p>
              </div>
            </div>
            <FollowButton
              userId={follower.id}
              initialIsFollowing={follower.is_following}
            />
          </div>
        ))}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <i className="fas fa-spinner fa-spin"></i> Loading...
        </div>
      )}

      {hasMore && !loading && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <button className="btn" onClick={() => setPage(prev => prev + 1)}>
            Load More
          </button>
        </div>
      )}

      {!loading && followers.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-users" style={{ fontSize: '48px', color: '#ccc' }}></i>
          <p style={{ marginTop: '20px', color: '#999' }}>No followers yet</p>
        </div>
      )}
    </div>
  );
};

export default FollowersPage;
