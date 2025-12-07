import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const getAuthHeaders = (token) => ({
  headers: { Authorization: `Bearer ${token}` }
});

// Get all conversations
export const getConversations = async (token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/chat/conversations/`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Get or create conversation with a user
export const getOrCreateConversation = async (otherUserId, token) => {
  try {
    const response = await axios.post(
      `${API_BASE}/chat/conversations/${otherUserId}/`,
      {},
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Get messages in a conversation
export const getMessages = async (conversationId, page = 1, token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/chat/messages/${conversationId}/?page=${page}`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Send a message
export const sendMessage = async (conversationId, content, token) => {
  try {
    const response = await axios.post(
      `${API_BASE}/chat/messages/${conversationId}/send/`,
      { content },
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// Get unread messages count
export const getUnreadMessagesCount = async (token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/chat/unread-count/`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};
