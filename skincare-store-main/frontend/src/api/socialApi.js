import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

// Helper to get auth headers
const getAuthHeaders = (token) => ({
  headers: { Authorization: `Bearer ${token}` }
});

// ============================================================================
// FOLLOW/UNFOLLOW
// ============================================================================

export const followUser = async (userId, token) => {
  try {
    const response = await axios.post(
      `${API_BASE}/social/follow/${userId}/`,
      {},
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const unfollowUser = async (userId, token) => {
  try {
    const response = await axios.post(
      `${API_BASE}/social/unfollow/${userId}/`,
      {},
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// ============================================================================
// USER PROFILE & DISCOVERY
// ============================================================================

export const getUserProfile = async (userId, token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/social/users/${userId}/profile/`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const searchUsers = async (query, page = 1, token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/social/users/search/?q=${encodeURIComponent(query)}&page=${page}`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getSuggestedUsers = async (token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/social/users/suggested/`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// ============================================================================
// FOLLOWERS & FOLLOWING
// ============================================================================

export const getFollowers = async (userId, page = 1, token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/social/followers/${userId}/?page=${page}`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getFollowing = async (userId, page = 1, token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/social/following/${userId}/?page=${page}`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getMutualFollowers = async (userId, token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/social/users/${userId}/mutual-followers/`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

// ============================================================================
// NOTIFICATIONS
// ============================================================================

export const getNotifications = async (page = 1, isRead = null, token) => {
  try {
    let url = `${API_BASE}/social/notifications/?page=${page}`;
    if (isRead !== null) {
      url += `&is_read=${isRead}`;
    }
    const response = await axios.get(url, getAuthHeaders(token));
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getUnreadNotificationsCount = async (token) => {
  try {
    const response = await axios.get(
      `${API_BASE}/social/notifications/unread-count/`,
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const markNotificationRead = async (notificationId, token) => {
  try {
    const response = await axios.post(
      `${API_BASE}/social/notifications/${notificationId}/read/`,
      {},
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const markAllNotificationsRead = async (token) => {
  try {
    const response = await axios.post(
      `${API_BASE}/social/notifications/mark-all-read/`,
      {},
      getAuthHeaders(token)
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};
