import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getFollowing } from '../api/socialApi';
import FollowButton from '../components/FollowButton';

const FollowingPage = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [following, setFollowing] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    fetchFollowing();
  }, [userId, page]);

  const fetchFollowing = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const data = await getFollowing(userId, page, token);
      setFollowing(prev => page === 1 ? data.following : [...prev, ...data.following]);
      setHasMore(data.has_more);
    } catch (error) {
      console.error('Error fetching following:', error);
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
        <h2>Following</h2>
      </div>

      <div className="users-list">
        {following.map(user => (
          <div key={user.id} className="user-item">
            <div className="user-item-left" onClick={() => navigate(`/users/${user.id}/profile`)}>
              <i className="fas fa-user-circle user-avatar"></i>
              <div className="user-item-info">
                <h4>{user.name}</h4>
                <p>{user.email}</p>
                {user.bio && <p className="user-bio">{user.bio}</p>}
                <p className="user-stats">
                  {user.followers_count} followers · {user.following_count} following
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

      {!loading && following.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-user-friends" style={{ fontSize: '48px', color: '#ccc' }}></i>
          <p style={{ marginTop: '20px', color: '#999' }}>Not following anyone yet</p>
        </div>
      )}
    </div>
  );
};

export default FollowingPage;
