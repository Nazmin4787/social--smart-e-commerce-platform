import React, { useState, useContext } from 'react';
import { followUser, unfollowUser } from '../api/socialApi';
import { AuthContext } from '../context/AuthContext';

const FollowButton = ({ userId, initialIsFollowing = false, onFollowChange }) => {
  const { user } = useContext(AuthContext);
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);
  const [loading, setLoading] = useState(false);

  // Don't show follow button for admins
  if (user && (user.is_staff || user.is_superuser)) {
    return null;
  }

  const handleFollowToggle = async () => {
    if (!user) {
      alert('Please login to follow users');
      return;
    }

    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      if (isFollowing) {
        await unfollowUser(userId, token);
        setIsFollowing(false);
        if (onFollowChange) onFollowChange(false);
      } else {
        await followUser(userId, token);
        setIsFollowing(true);
        if (onFollowChange) onFollowChange(true);
      }
    } catch (error) {
      console.error('Follow/unfollow error:', error);
      alert(error.error || 'Failed to update follow status');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className={`follow-btn ${isFollowing ? 'following' : 'not-following'}`}
      onClick={handleFollowToggle}
      disabled={loading}
    >
      {loading ? (
        <span>
          <i className="fas fa-spinner fa-spin"></i> Loading...
        </span>
      ) : isFollowing ? (
        <span>
          <i className="fas fa-user-check"></i> Following
        </span>
      ) : (
        <span>
          <i className="fas fa-user-plus"></i> Follow
        </span>
      )}
    </button>
  );
};

export default FollowButton;
