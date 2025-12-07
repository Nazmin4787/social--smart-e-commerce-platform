# Frontend Implementation Guide - Social Features

## 🎯 What's Been Built (Backend)

✅ Complete follow/unfollow system
✅ User profiles with social stats
✅ User search and discovery
✅ Notifications system
✅ All API endpoints ready
✅ Test data seeded

---

## 📋 Frontend To-Do List

### 1. **API Integration Layer**
Create `src/api/socialApi.js`:

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

// Follow/Unfollow
export const followUser = (userId, token) => 
  axios.post(`${API_BASE}/social/follow/${userId}/`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });

export const unfollowUser = (userId, token) => 
  axios.post(`${API_BASE}/social/unfollow/${userId}/`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });

// User Profile
export const getUserProfile = (userId, token) => 
  axios.get(`${API_BASE}/social/users/${userId}/profile/`, {
    headers: { Authorization: `Bearer ${token}` }
  });

// Followers/Following
export const getFollowers = (userId, page = 1, token) => 
  axios.get(`${API_BASE}/social/followers/${userId}/?page=${page}`, {
    headers: { Authorization: `Bearer ${token}` }
  });

export const getFollowing = (userId, page = 1, token) => 
  axios.get(`${API_BASE}/social/following/${userId}/?page=${page}`, {
    headers: { Authorization: `Bearer ${token}` }
  });

// Search & Discovery
export const searchUsers = (query, page = 1, token) => 
  axios.get(`${API_BASE}/social/users/search/?q=${query}&page=${page}`, {
    headers: { Authorization: `Bearer ${token}` }
  });

export const getSuggestedUsers = (token) => 
  axios.get(`${API_BASE}/social/users/suggested/`, {
    headers: { Authorization: `Bearer ${token}` }
  });

// Notifications
export const getNotifications = (page = 1, isRead = null, token) => {
  let url = `${API_BASE}/social/notifications/?page=${page}`;
  if (isRead !== null) url += `&is_read=${isRead}`;
  return axios.get(url, {
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const getUnreadCount = (token) => 
  axios.get(`${API_BASE}/social/notifications/unread-count/`, {
    headers: { Authorization: `Bearer ${token}` }
  });

export const markNotificationRead = (notificationId, token) => 
  axios.post(`${API_BASE}/social/notifications/${notificationId}/read/`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });

export const markAllNotificationsRead = (token) => 
  axios.post(`${API_BASE}/social/notifications/mark-all-read/`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
```

---

### 2. **Components to Create**

#### A. **FollowButton.js**
```javascript
// Reusable follow/unfollow button
- Shows "Follow" or "Following" based on state
- Handles follow/unfollow API calls
- Shows loading state during API call
- Updates follower count optimistically
```

#### B. **UserProfilePage.js**
```javascript
// User profile page (Instagram-style)
- Display user info (name, email, bio)
- Show followers/following counts (clickable)
- Display liked products count
- Show mutual followers count
- Follow/Unfollow button
- Grid of liked products (optional)
```

#### C. **FollowersModal.js** or **FollowersPage.js**
```javascript
// List of followers
- Display followers with avatar, name, bio
- Follow/Unfollow button for each user
- Infinite scroll or pagination
- Show mutual followers badge
- Click user to view their profile
```

#### D. **FollowingModal.js** or **FollowingPage.js**
```javascript
// List of following
- Similar to FollowersModal
- Show "Following" button (allows unfollow)
- Infinite scroll or pagination
```

#### E. **UserSearchPage.js**
```javascript
// Search users page
- Search input with debouncing
- Display search results
- Follow/Unfollow button for each result
- Show mutual followers count
- Click user to view profile
```

#### F. **SuggestedUsers.js**
```javascript
// Suggested users to follow section
- Display 5-10 suggested users
- Show as carousel or grid
- Follow button for each
- Show follower count
- "See All" link to full suggestions page
```

#### G. **NotificationBell.js**
```javascript
// Notification bell icon in header
- Show unread count badge
- Click to open dropdown
- Display recent 5 notifications
- "See All" link to full notifications page
- Mark as read on click
```

#### H. **NotificationsPage.js**
```javascript
// Full notifications page
- List all notifications
- Filter by read/unread
- Mark individual as read
- Mark all as read button
- Show actor avatar, name, action
- Click to view actor's profile
- Pagination or infinite scroll
```

#### I. **MutualFollowersSection.js**
```javascript
// Show mutual followers
- Display in user profile
- Show avatars/names of mutual connections
- "X mutual followers" text
- Click to see full list
```

---

### 3. **Update Existing Components**

#### **Header.js**
```javascript
// Add to header:
- NotificationBell component
- User search icon/input
- Link to user's own profile
```

#### **ProfilePage.js** (Current user's profile)
```javascript
// Add social stats:
- Followers count (clickable)
- Following count (clickable)
- Edit profile button
- Settings/privacy options
```

---

### 4. **Routes to Add**

```javascript
// In App.js or routing file:
import UserProfilePage from './pages/UserProfilePage';
import FollowersPage from './pages/FollowersPage';
import FollowingPage from './pages/FollowingPage';
import UserSearchPage from './pages/UserSearchPage';
import NotificationsPage from './pages/NotificationsPage';

<Route path="/users/:userId/profile" element={<UserProfilePage />} />
<Route path="/users/:userId/followers" element={<FollowersPage />} />
<Route path="/users/:userId/following" element={<FollowingPage />} />
<Route path="/search/users" element={<UserSearchPage />} />
<Route path="/notifications" element={<NotificationsPage />} />
```

---

### 5. **Styling Guidelines**

#### Follow Button States:
```css
/* Not following */
.btn-follow {
  background: #0095f6; /* Instagram blue */
  color: white;
}

/* Following */
.btn-following {
  background: transparent;
  border: 1px solid #dbdbdb;
  color: #262626;
}

/* Hover on following */
.btn-following:hover {
  background: #fafafa;
}
```

#### Notification Badge:
```css
.notification-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ff3b30; /* Red */
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 12px;
}
```

#### User Profile Layout:
```
┌─────────────────────────────────┐
│  Avatar    Name                 │
│            @email               │
│            Bio text...          │
│                                 │
│  120       450      35          │
│  Followers Following Liked      │
│                                 │
│  [Follow Button]                │
│  8 mutual followers             │
└─────────────────────────────────┘
```

---

### 6. **State Management**

Consider using Context API or Redux for:
- Current user's follow list (to show follow status)
- Notification count (updates across app)
- User profile cache

Example Context:
```javascript
// SocialContext.js
const SocialContext = createContext();

export const SocialProvider = ({ children }) => {
  const [followingIds, setFollowingIds] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Methods to update state
  const addFollowing = (userId) => {...};
  const removeFollowing = (userId) => {...};
  const updateNotificationCount = () => {...};
  
  return (
    <SocialContext.Provider value={{
      followingIds,
      unreadCount,
      addFollowing,
      removeFollowing,
      updateNotificationCount
    }}>
      {children}
    </SocialContext.Provider>
  );
};
```

---

### 7. **UX Enhancements**

- **Optimistic Updates**: Update UI immediately, revert on error
- **Loading States**: Show spinners during API calls
- **Error Handling**: Toast notifications for errors
- **Empty States**: Show helpful messages when no data
- **Infinite Scroll**: Load more on scroll for lists
- **Search Debouncing**: Wait 300ms after typing to search
- **Real-time Updates**: Poll notification count every 30 seconds
- **Skeleton Loaders**: Show loading placeholders

---

### 8. **Priority Implementation Order**

1. **Phase 1 - Core Features** (Start Here)
   - FollowButton component
   - UserProfilePage
   - Update ProfilePage with social stats

2. **Phase 2 - Discovery**
   - UserSearchPage
   - SuggestedUsers component

3. **Phase 3 - Social Lists**
   - FollowersPage/Modal
   - FollowingPage/Modal
   - MutualFollowers

4. **Phase 4 - Notifications**
   - NotificationBell
   - NotificationsPage
   - Notification polling

---

### 9. **Testing Checklist**

- [ ] Can follow/unfollow users
- [ ] Follow button shows correct state
- [ ] Follower counts update correctly
- [ ] Can view user profiles
- [ ] Search returns correct results
- [ ] Suggested users appear
- [ ] Notifications display correctly
- [ ] Can mark notifications as read
- [ ] Notification count updates
- [ ] Can navigate between users
- [ ] Mutual followers display
- [ ] Loading states work
- [ ] Error messages display

---

### 10. **API Endpoints Summary**

```
POST   /api/social/follow/<user_id>/
POST   /api/social/unfollow/<user_id>/
GET    /api/social/followers/<user_id>/
GET    /api/social/following/<user_id>/
GET    /api/social/users/<user_id>/profile/
GET    /api/social/users/<user_id>/mutual-followers/
GET    /api/social/users/search/?q=<query>
GET    /api/social/users/suggested/
GET    /api/social/notifications/
GET    /api/social/notifications/unread-count/
POST   /api/social/notifications/<id>/read/
POST   /api/social/notifications/mark-all-read/
```

---

## 🎨 Design Inspiration

Look at Instagram's web interface for:
- User profile layout
- Follow button styles
- Followers/Following modals
- Notification dropdown
- Search results display

---

## 🚀 Getting Started

1. **Test Backend First**: Use Postman/curl to test endpoints
2. **Create API Layer**: Build socialApi.js first
3. **Build Core Components**: Start with FollowButton
4. **Add Routes**: Set up routing for new pages
5. **Style Components**: Use existing styles.css patterns
6. **Test Integration**: Verify all features work end-to-end

---

**The backend is 100% ready. Start building the frontend! 🎉**
