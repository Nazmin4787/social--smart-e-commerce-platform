# Social Features API Documentation

## 🎯 Overview
Instagram/Facebook-style social networking features for the skincare e-commerce platform.

---

## 🔐 Authentication
All endpoints require JWT Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 📋 API Endpoints

### 1. **Follow a User**
**POST** `/api/social/follow/<user_id>/`

**Request:**
```json
Headers: Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "You are now following John Doe",
  "followers_count": 15,
  "following_count": 8
}
```

**Errors:**
- 400: "You cannot follow yourself"
- 400: "Already following this user"
- 404: "User not found"

---

### 2. **Unfollow a User**
**POST** `/api/social/unfollow/<user_id>/`

**Request:**
```json
Headers: Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "You unfollowed John Doe",
  "followers_count": 14,
  "following_count": 7
}
```

**Errors:**
- 400: "You are not following this user"
- 404: "User not found"

---

### 3. **Get User's Followers**
**GET** `/api/social/followers/<user_id>/`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response:**
```json
{
  "followers": [
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "bio": "Skincare enthusiast",
      "followers_count": 120,
      "following_count": 85,
      "is_following": true,
      "mutual_followers_count": 5
    }
  ],
  "total_count": 50,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

---

### 4. **Get User's Following List**
**GET** `/api/social/following/<user_id>/`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response:**
```json
{
  "following": [
    {
      "id": 3,
      "name": "Alex Johnson",
      "email": "alex@example.com",
      "bio": "Beauty blogger",
      "followers_count": 200,
      "following_count": 150,
      "is_following": false,
      "mutual_followers_count": 3
    }
  ],
  "total_count": 30,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

---

### 5. **Get User Profile (with Social Stats)**
**GET** `/api/social/users/<user_id>/profile/`

**Response:**
```json
{
  "id": 5,
  "name": "Sarah Williams",
  "email": "sarah@example.com",
  "bio": "Passionate about natural skincare",
  "followers_count": 340,
  "following_count": 120,
  "is_following": true,
  "mutual_followers_count": 8,
  "liked_products_count": 25
}
```

---

### 6. **Search Users**
**GET** `/api/social/users/search/`

**Query Parameters:**
- `q` (required): Search query (min 2 characters)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Example:** `/api/social/users/search/?q=john&page=1`

**Response:**
```json
{
  "users": [
    {
      "id": 7,
      "name": "John Miller",
      "email": "john.miller@example.com",
      "bio": "Skincare expert",
      "followers_count": 89,
      "following_count": 45,
      "is_following": false,
      "mutual_followers_count": 2
    }
  ],
  "total_count": 5,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

**Errors:**
- 400: "Search query must be at least 2 characters"

---

### 7. **Get Suggested Users to Follow**
**GET** `/api/social/users/suggested/`

**Response:**
```json
{
  "suggested_users": [
    {
      "id": 12,
      "name": "Emily Davis",
      "email": "emily@example.com",
      "bio": "Beauty content creator",
      "followers_count": 450,
      "following_count": 200,
      "is_following": false,
      "mutual_followers_count": 10
    }
  ]
}
```

*Returns up to 20 users sorted by follower count*

---

### 8. **Get Mutual Followers**
**GET** `/api/social/users/<user_id>/mutual-followers/`

**Response:**
```json
{
  "mutual_followers": [
    {
      "id": 15,
      "name": "Michael Brown",
      "email": "michael@example.com",
      "bio": "Skincare lover",
      "followers_count": 67,
      "following_count": 89,
      "is_following": true,
      "mutual_followers_count": 4
    }
  ],
  "count": 8
}
```

---

### 9. **Get Notifications**
**GET** `/api/social/notifications/`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `is_read` (optional): Filter by read status ("true" or "false")

**Example:** `/api/social/notifications/?is_read=false&page=1`

**Response:**
```json
{
  "notifications": [
    {
      "id": 42,
      "actor": {
        "id": 8,
        "name": "Lisa Anderson",
        "email": "lisa@example.com",
        "bio": "Beauty enthusiast"
      },
      "notification_type": "follow",
      "message": "Lisa Anderson started following you",
      "is_read": false,
      "created_at": "2025-12-05T10:30:00Z"
    }
  ],
  "total_count": 15,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

---

### 10. **Get Unread Notifications Count**
**GET** `/api/social/notifications/unread-count/`

**Response:**
```json
{
  "unread_count": 7
}
```

*Perfect for notification badge counters*

---

### 11. **Mark Notification as Read**
**POST** `/api/social/notifications/<notification_id>/read/`

**Response:**
```json
{
  "message": "Notification marked as read",
  "unread_count": 6
}
```

**Errors:**
- 404: "Notification not found"

---

### 12. **Mark All Notifications as Read**
**POST** `/api/social/notifications/mark-all-read/`

**Response:**
```json
{
  "message": "15 notifications marked as read",
  "unread_count": 0
}
```

---

## 🧪 Testing with curl

### Get user profile:
```bash
curl -X GET http://localhost:8000/api/social/users/1/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Follow a user:
```bash
curl -X POST http://localhost:8000/api/social/follow/2/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search users:
```bash
curl -X GET "http://localhost:8000/api/social/users/search/?q=test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get notifications:
```bash
curl -X GET http://localhost:8000/api/social/notifications/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get unread count:
```bash
curl -X GET http://localhost:8000/api/social/notifications/unread-count/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 Database Models

### UserFollow
```python
- follower: FK to AppUser (who is following)
- following: FK to AppUser (who is being followed)
- created_at: DateTime
- unique_together: (follower, following)
```

### Notification
```python
- user: FK to AppUser (recipient)
- actor: FK to AppUser (who performed action)
- notification_type: CharField (choices: 'follow')
- message: TextField
- is_read: Boolean (default: False)
- created_at: DateTime
```

### AppUser (Enhanced)
```python
Methods:
- get_followers_count()
- get_following_count()
- is_following(user_id)
- get_mutual_followers_count(other_user_id)
- to_profile_dict(requesting_user=None)
```

---

## 🎨 Frontend Integration Ideas

### Components to Build:
1. **UserProfile Component** - Display user info with follow button
2. **FollowersList Component** - Show followers with infinite scroll
3. **FollowingList Component** - Show following with infinite scroll
4. **UserSearchBar Component** - Search users with autocomplete
5. **SuggestedUsers Component** - Carousel/grid of suggestions
6. **NotificationBell Component** - Badge with dropdown
7. **NotificationList Component** - Full notifications page
8. **FollowButton Component** - Reusable follow/unfollow button
9. **MutualFollowers Component** - Show mutual connections

### UI/UX Features:
- Real-time notification count updates
- Optimistic UI updates for follow/unfollow
- Infinite scroll for lists
- Search debouncing
- Loading states and skeletons
- Error handling and retry logic
- Toast notifications for actions

---

## ✅ Current Status

- ✅ 19/20 tasks completed
- ✅ All models created and migrated
- ✅ All API endpoints implemented
- ✅ Authentication integrated
- ✅ Admin panel configured
- ✅ Test data seeded (17 follow relationships, 17 notifications)
- ✅ Server running on http://localhost:8000

---

## 🚀 Quick Start

1. **Server is already running** on `http://localhost:8000`
2. **Login to get JWT token:**
   ```bash
   POST /api/auth/login/
   Body: {"email": "user@example.com", "password": "password"}
   ```
3. **Use token in all social endpoints**
4. **Test with existing users** (5 users with follow relationships already seeded)

---

## 📝 Notes

- All endpoints return JSON responses
- Pagination defaults to 20 items per page
- Timestamps are in ISO 8601 format
- Follow relationships prevent self-follows and duplicates
- Notifications are automatically created on follow
- Search requires minimum 2 characters
- Suggested users limited to 20 max (sorted by popularity)

---

**Happy Coding! 🎉**
