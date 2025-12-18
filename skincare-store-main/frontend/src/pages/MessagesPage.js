import React, { useState, useEffect, useContext, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { CartContext } from '../context/CartContext';
import { getConversations, getMessages, sendMessage } from '../api/chatApi';
import Header from '../components/Header';
import ShareButton from '../components/ShareButton';
import axios from 'axios';

const MessagesPage = () => {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const { user } = useContext(AuthContext);
  const { addItem } = useContext(CartContext);
  
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const [editingMessage, setEditingMessage] = useState(null);
  const [likedProducts, setLikedProducts] = useState(new Set());
  const messagesEndRef = useRef(null);
  const messageInputRef = useRef(null);
  const lastFetchedConvId = useRef(null);

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }

    if (user.is_staff && user.is_superuser) {
      return;
    }

    fetchConversations();
  }, [user, navigate]);

  useEffect(() => {
    if (conversationId && conversations.length > 0) {
      const conv = conversations.find(c => c.id === parseInt(conversationId));
      if (conv) {
        setSelectedConversation(conv);
        if (lastFetchedConvId.current !== parseInt(conversationId)) {
          lastFetchedConvId.current = parseInt(conversationId);
          fetchMessages(parseInt(conversationId));
        }
      }
    }
  }, [conversationId, conversations]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const data = await getConversations(token);
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (convId) => {
    const token = localStorage.getItem('access_token');

    try {
      const data = await getMessages(convId, 1, token);
      console.log('Fetched messages:', data.messages);
      console.log('Current user ID:', user.id);
      setMessages(data.messages || []);
      
      // Fetch liked status for all products in messages
      const productIds = data.messages
        ?.filter(msg => msg.message_type === 'product' && msg.shared_product)
        .map(msg => msg.shared_product.id) || [];
      
      if (productIds.length > 0) {
        await fetchLikedProducts(productIds);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const fetchLikedProducts = async (productIds) => {
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await axios.get('http://localhost:8000/api/liked-products/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Response is an array of objects with {id, product: {id, ...}}
      const likedProductIds = response.data.map(item => item.product.id);
      const likedSet = new Set(likedProductIds.filter(id => productIds.includes(id)));
      setLikedProducts(likedSet);
    } catch (error) {
      console.error('Error fetching liked products:', error);
    }
  };

  const handleSelectConversation = (conversation) => {
    setSelectedConversation(conversation);
    navigate(`/messages/${conversation.id}`);
  };

  const handleLikeProduct = async (e, productId) => {
    e.stopPropagation();
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await axios.post(
        `http://localhost:8000/api/liked-products/toggle/`,
        { product_id: productId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Toggle the liked state
      setLikedProducts(prev => {
        const newSet = new Set(prev);
        if (newSet.has(productId)) {
          newSet.delete(productId);
        } else {
          newSet.add(productId);
        }
        return newSet;
      });
    } catch (error) {
      console.error('Error liking product:', error);
    }
  };

  const handleAddToCart = async (e, product) => {
    e.stopPropagation();
    
    try {
      await addItem(product, 1);
      navigate('/cart');
    } catch (error) {
      console.error('Error adding to cart:', error);
      if (error.message === 'Not authenticated') {
        alert('Please log in to add items to cart');
      } else {
        alert('Failed to add product to cart');
      }
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!messageText.trim() || !selectedConversation || sending) return;

    // If editing, update the message instead
    if (editingMessage) {
      await handleUpdateMessage();
      return;
    }

    setSending(true);
    const token = localStorage.getItem('access_token');
    const tempMessage = {
      id: Date.now(),
      content: messageText,
      sender: { id: user.id, name: user.name },
      created_at: new Date().toISOString(),
      is_read: false
    };

    setMessages(prev => [...prev, tempMessage]);
    setMessageText('');

    try {
      const data = await sendMessage(selectedConversation.id, messageText, token);
      setMessages(prev => 
        prev.map(msg => msg.id === tempMessage.id ? data.message : msg)
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.filter(msg => msg.id !== tempMessage.id));
      alert(error.error || 'Failed to send message');
    } finally {
      setSending(false);
      messageInputRef.current?.focus();
    }
  };

  const handleContextMenu = (e, message) => {
    e.preventDefault();
    if (message.sender.id !== user.id) return; // Only show menu for own messages
    
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      message: message
    });
  };

  const handleEditMessage = (e) => {
    e.stopPropagation();
    if (contextMenu && contextMenu.message) {
      setEditingMessage(contextMenu.message);
      setMessageText(contextMenu.message.content);
      setContextMenu(null);
      messageInputRef.current?.focus();
    }
  };

  const handleDeleteMessage = async (e) => {
    e.stopPropagation();
    if (!contextMenu || !contextMenu.message) return;
    
    const messageId = contextMenu.message.id;
    setContextMenu(null);
    
    if (!window.confirm('Are you sure you want to delete this message?')) return;
    
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch(`http://localhost:8000/api/chat/messages/${messageId}/delete/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        setMessages(prev => prev.filter(msg => msg.id !== messageId));
      } else {
        alert('Failed to delete message');
      }
    } catch (error) {
      console.error('Error deleting message:', error);
      alert('Failed to delete message');
    }
  };

  const handleUpdateMessage = async () => {
    if (!editingMessage || !messageText.trim()) return;
    
    const token = localStorage.getItem('access_token');
    setSending(true);
    
    try {
      const response = await fetch(`http://localhost:8000/api/chat/messages/${editingMessage.id}/edit/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: messageText })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => 
          prev.map(msg => msg.id === editingMessage.id ? data.message : msg)
        );
        setEditingMessage(null);
        setMessageText('');
      } else {
        alert('Failed to update message');
      }
    } catch (error) {
      console.error('Error updating message:', error);
      alert('Failed to update message');
    } finally {
      setSending(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingMessage(null);
    setMessageText('');
  };

  useEffect(() => {
    const handleClick = (e) => {
      if (!e.target.closest('.message-context-menu')) {
        setContextMenu(null);
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatMessageTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  if (user && (user.is_staff && user.is_superuser)) {
    return (
      <>
        <Header />
        <div className="messages-page">
          <div className="admin-restriction-message">
            <i className="fas fa-user-shield"></i>
            <h2>Admin Access Only</h2>
            <p>Messaging is only available to regular users.</p>
            <button className="btn-primary" onClick={() => navigate('/')}>
              Go to Home
            </button>
          </div>
        </div>

        {/* Context Menu */}
        {contextMenu && (
          <div 
            className="message-context-menu"
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              top: `${contextMenu.y}px`,
              left: `${contextMenu.x}px`,
              zIndex: 1000
            }}
          >
            <button onClick={handleEditMessage}>
              <i className="fas fa-edit"></i> Edit
            </button>
            <button onClick={handleDeleteMessage} className="delete-btn">
              <i className="fas fa-trash"></i> Delete
            </button>
          </div>
        )}
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="messages-page">
        <div className="messages-container">
          {/* Conversations Sidebar */}
          <div className="conversations-sidebar">
            <div className="sidebar-header">
              <h2>
                <i className="fas fa-comments"></i> Messages
              </h2>
            </div>
            
            <div className="conversations-list">
              {loading ? (
                <div className="loading-conversations">
                  <div className="spinner"></div>
                  <p>Loading...</p>
                </div>
              ) : conversations.length === 0 ? (
                <div className="empty-conversations">
                  <i className="fas fa-inbox"></i>
                  <p>No conversations yet</p>
                  <button className="btn-secondary" onClick={() => navigate('/social')}>
                    Find Friends
                  </button>
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`conversation-item ${selectedConversation?.id === conv.id ? 'active' : ''}`}
                    onClick={() => handleSelectConversation(conv)}
                  >
                    <div className="conversation-avatar">
                      <i className="fas fa-user-circle"></i>
                      {conv.unread_count > 0 && (
                        <span className="unread-badge">{conv.unread_count}</span>
                      )}
                    </div>
                    <div className="conversation-info">
                      <h4>{conv.other_user.name}</h4>
                      {conv.last_message && (
                        <p className="last-message">
                          {conv.last_message.message_type === 'product' ? (
                            <>
                              <i className="fas fa-share-alt" style={{ marginRight: '6px' }}></i>
                              Shared a product
                            </>
                          ) : (
                            <>
                              {conv.last_message.content.length > 40
                                ? conv.last_message.content.substring(0, 40) + '...'
                                : conv.last_message.content}
                            </>
                          )}
                        </p>
                      )}
                    </div>
                    {conv.last_message && (
                      <span className="conversation-time">
                        {formatTime(conv.updated_at)}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Chat Area */}
          <div className="chat-area">
            {selectedConversation ? (
              <>
                {/* Chat Header */}
                <div className="chat-header">
                  <div className="chat-user-info" onClick={() => navigate(`/users/${selectedConversation.other_user.id}/profile`)}>
                    <div className="chat-avatar">
                      <i className="fas fa-user-circle"></i>
                    </div>
                    <div>
                      <h3>{selectedConversation.other_user.name}</h3>
                      <p>{selectedConversation.other_user.email}</p>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="messages-area">
                  {messages.length === 0 ? (
                    <div className="no-messages">
                      <i className="fas fa-comments"></i>
                      <p>No messages yet</p>
                      <span>Start the conversation!</span>
                    </div>
                  ) : (
                    <div className="messages-list">
                      {messages.map((message, index) => {
                        const isOwn = message.sender.id === user.id;
                        const showDate = index === 0 || 
                          new Date(messages[index - 1].created_at).toDateString() !== 
                          new Date(message.created_at).toDateString();

                        return (
                          <React.Fragment key={message.id}>
                            {showDate && (
                              <div className="message-date">
                                {new Date(message.created_at).toLocaleDateString('en-US', {
                                  weekday: 'long',
                                  year: 'numeric',
                                  month: 'long',
                                  day: 'numeric'
                                })}
                              </div>
                            )}
                            <div 
                              className={`message ${isOwn ? 'own' : 'other'}`}
                              onContextMenu={(e) => handleContextMenu(e, message)}
                            >
                              {message.message_type === 'product' && message.shared_product ? (
                                // Product Share Message
                                <div className="message-bubble product-share">
                                  {message.content && (
                                    <p className="share-message">{message.content}</p>
                                  )}
                                  <div className="shared-product-card">
                                    <div className="product-image-container">
                                      <img 
                                        src={
                                          message.shared_product.images && message.shared_product.images.length > 0
                                            ? (message.shared_product.images[0].startsWith('http') 
                                                ? message.shared_product.images[0] 
                                                : `http://localhost:8000${message.shared_product.images[0]}`)
                                            : '/placeholder.png'
                                        }
                                        alt={message.shared_product.title}
                                        className="shared-product-image"
                                        onClick={() => navigate(`/products/${message.shared_product.id}`)}
                                        onError={(e) => { e.target.src = '/placeholder.png'; }}
                                      />
                                      <div className="product-action-icons">
                                        <button 
                                          className={`like-button ${likedProducts.has(message.shared_product.id) ? 'liked' : ''}`}
                                          onClick={(e) => handleLikeProduct(e, message.shared_product.id)}
                                          title="Like"
                                        >
                                          <i className={likedProducts.has(message.shared_product.id) ? 'fas fa-heart' : 'far fa-heart'}></i>
                                        </button>
                                        <div onClick={(e) => e.stopPropagation()}>
                                          <ShareButton product={message.shared_product} iconOnly={true} className="share-in-chat" />
                                        </div>
                                      </div>
                                    </div>
                                    <div className="shared-product-info">
                                      <h4 
                                        className="shared-product-title"
                                        onClick={() => navigate(`/products/${message.shared_product.id}`)}
                                      >
                                        {message.shared_product.title}
                                      </h4>
                                      <p className="shared-product-price">₹{message.shared_product.price}</p>
                                      <div className="product-card-footer">
                                        {message.shared_product.stock > 0 ? (
                                          <span className="shared-product-stock in-stock">
                                            <i className="fas fa-check-circle"></i> In Stock
                                          </span>
                                        ) : (
                                          <span className="shared-product-stock out-of-stock">
                                            <i className="fas fa-times-circle"></i> Out of Stock
                                          </span>
                                        )}
                                        <button 
                                          className="add-to-cart-btn-small"
                                          onClick={(e) => handleAddToCart(e, message.shared_product)}
                                          disabled={message.shared_product.stock === 0}
                                        >
                                          <i className="fas fa-shopping-cart"></i>
                                        </button>
                                      </div>
                                    </div>
                                  </div>
                                  <span className="message-time">
                                    {formatMessageTime(message.created_at)}
                                  </span>
                                </div>
                              ) : (
                                // Regular Text Message
                                <div className="message-bubble">
                                  <p>{message.content}</p>
                                  <span className="message-time">
                                    {formatMessageTime(message.created_at)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </React.Fragment>
                        );
                      })}
                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </div>

                {/* Message Input */}
                <form className="message-input-area" onSubmit={handleSendMessage}>
                  {editingMessage && (
                    <div className="editing-indicator">
                      <span>
                        <i className="fas fa-edit"></i> Editing message
                      </span>
                      <button type="button" onClick={handleCancelEdit} className="cancel-edit-btn">
                        <i className="fas fa-times"></i>
                      </button>
                    </div>
                  )}
                  <div className="input-wrapper">
                    <input
                      ref={messageInputRef}
                      type="text"
                      placeholder={editingMessage ? "Edit your message..." : "Type a message..."}
                      value={messageText}
                      onChange={(e) => setMessageText(e.target.value)}
                      disabled={sending}
                    />
                    <button 
                      type="submit" 
                      className="send-btn" 
                      disabled={!messageText.trim() || sending}
                    >
                      {sending ? (
                        <i className="fas fa-spinner fa-spin"></i>
                      ) : (
                        <i className="fas fa-paper-plane"></i>
                      )}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="no-conversation-selected">
                <i className="fas fa-comment-dots"></i>
                <h3>Select a conversation</h3>
                <p>Choose a conversation from the left to start messaging</p>
              </div>
            )}
          </div>
        </div>

        {/* Context Menu */}
        {contextMenu && (
          <div 
            className="message-context-menu"
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              top: `${contextMenu.y}px`,
              left: `${contextMenu.x}px`,
              zIndex: 1000
            }}
          >
            <button onClick={handleEditMessage}>
              <i className="fas fa-edit"></i> Edit
            </button>
            <button onClick={handleDeleteMessage} className="delete-btn">
              <i className="fas fa-trash"></i> Delete
            </button>
          </div>
        )}
      </div>
    </>
  );
};

export default MessagesPage;
