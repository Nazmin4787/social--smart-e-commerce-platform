import React, { useState, useEffect } from 'react';
import { getMutualFollowers } from '../api/socialApi';
import { shareProduct } from '../api';
import { useNavigate } from 'react-router-dom';

function ShareProductModal({ isOpen, onClose, product }) {
  const [followers, setFollowers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sharing, setSharing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (isOpen) {
      loadMutualFollowers();
      setMessage('');
      setSelectedUser(null);
      setSearchQuery('');
    }
  }, [isOpen]);

  const loadMutualFollowers = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.log('No token found');
      return;
    }

    setLoading(true);
    try {
      // Get my user ID from token
      const payload = JSON.parse(atob(token.split('.')[1]));
      const myId = payload.user_id;
      console.log('My user ID:', myId);

      // Get mutual followers (friends)
      const response = await getMutualFollowers(myId, token);
      console.log('Mutual followers response:', response);
      
      if (response && response.mutual_followers) {
        console.log('Setting mutual followers:', response.mutual_followers);
        setFollowers(response.mutual_followers);
      } else {
        console.log('No mutual_followers in response');
        setFollowers([]);
      }
    } catch (error) {
      console.error('Error loading mutual followers:', error);
      console.error('Error details:', error.response?.data);
      setFollowers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    if (!selectedUser) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Please login to share products');
      return;
    }

    setSharing(true);
    try {
      console.log('Sharing product:', {
        productId: product.id,
        recipientId: selectedUser.id,
        message: message
      });
      
      const response = await shareProduct(token, product.id, selectedUser.id, message);
      console.log('Share response:', response);
      
      alert(`Product shared with ${selectedUser.name}!`);
      onClose();
      
      // Optionally navigate to messages
      // navigate('/messages');
    } catch (error) {
      console.error('Error sharing product:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      const errorMessage = error.response?.data?.error || error.message || 'Failed to share product';
      alert(`Failed to share product: ${errorMessage}`);
    } finally {
      setSharing(false);
    }
  };

  const filteredFollowers = followers.filter(f =>
    f.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content share-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Share Product</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="share-product-info">
          <img 
            src={
              product.images && product.images.length > 0
                ? (product.images[0].startsWith('http') 
                    ? product.images[0] 
                    : `http://localhost:8000${product.images[0]}`)
                : '/placeholder.png'
            }
            alt={product.title}
            className="share-product-image"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = '/placeholder.png';
            }}
          />
          <div className="share-product-details">
            <h3>{product.title}</h3>
            <p className="share-product-price">₹{product.price}</p>
          </div>
        </div>

        <div className="share-modal-body">
          <div className="form-group">
            <label>Share with</label>
            <input
              type="text"
              placeholder="Search friends..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control search-input"
            />
          </div>

          {loading ? (
            <div className="loading-state">Loading friends...</div>
          ) : filteredFollowers.length === 0 ? (
            <div className="empty-state">
              {searchQuery ? 'No friends found matching your search.' : 'No mutual followers to share with.'}
            </div>
          ) : (
            <div className="followers-list">
              {filteredFollowers.map(follower => (
                <div
                  key={follower.id}
                  className={`follower-item ${selectedUser?.id === follower.id ? 'selected' : ''}`}
                  onClick={() => setSelectedUser(follower)}
                >
                  <div className="follower-avatar">
                    {follower.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="follower-info">
                    <div className="follower-name">{follower.name}</div>
                    <div className="follower-email">{follower.email}</div>
                  </div>
                  {selectedUser?.id === follower.id && (
                    <div className="check-icon">✓</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {selectedUser && (
            <div className="form-group message-box-section">
              <label>Add a message (optional)</label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Write something about this product..."
                rows="3"
                className="form-control"
                autoFocus
              />
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary"
            onClick={handleShare}
            disabled={!selectedUser || sharing}
          >
            {sharing ? 'Sharing...' : 'Share'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ShareProductModal;
