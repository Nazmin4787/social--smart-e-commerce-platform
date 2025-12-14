import React from 'react';

const FriendsActivity = ({ activities, friendsPurchased }) => {
  console.log('FriendsActivity component - activities:', activities);
  console.log('FriendsActivity component - friendsPurchased:', friendsPurchased);
  
  // Combine activities and purchases
  const allActivities = [];
  
  // Add like/cart activities
  if (activities && activities.length > 0) {
    allActivities.push(...activities);
  }
  
  // Add purchase activities
  if (friendsPurchased && friendsPurchased.length > 0) {
    const purchaseActivities = friendsPurchased.map(friend => ({
      user: {
        id: friend.id,
        name: friend.name,
        profile_picture: null
      },
      type: 'purchased',
      created_at: friend.purchased_date
    }));
    allActivities.push(...purchaseActivities);
  }
  
  if (allActivities.length === 0) {
    console.log('FriendsActivity - No activities to display');
    return null;
  }

  console.log('FriendsActivity - Displaying', allActivities.length, 'total activities');

  // Group by type
  const likedBy = allActivities.filter(a => a.type === 'liked');
  const purchasedBy = allActivities.filter(a => a.type === 'purchased');
  const cartBy = allActivities.filter(a => a.type === 'cart');
  
  // Check if there are both likes and purchases
  const hasBothLikedAndPurchased = likedBy.length > 0 && purchasedBy.length > 0;
  
  // Build activity text
  let activityText = '';
  let iconTypes = [];
  let displayActivities = [];
  let badgeClass = '';
  
  if (hasBothLikedAndPurchased) {
    // Combine likes and purchases
    const allUsers = [...likedBy, ...purchasedBy];
    const uniqueUserIds = new Set(allUsers.map(a => a.user.id));
    displayActivities = Array.from(uniqueUserIds).map(id => 
      allUsers.find(a => a.user.id === id)
    );
    
    if (uniqueUserIds.size === 1) {
      activityText = `${displayActivities[0].user.name} liked and purchased this`;
    } else if (uniqueUserIds.size === 2) {
      activityText = `${displayActivities[0].user.name} and ${displayActivities[1].user.name} liked and purchased this`;
    } else {
      activityText = `${displayActivities[0].user.name} and ${uniqueUserIds.size - 1} others liked and purchased this`;
    }
    iconTypes = ['liked', 'purchased'];
    badgeClass = 'purchased';
  } else if (purchasedBy.length > 0) {
    displayActivities = purchasedBy;
    const count = new Set(purchasedBy.map(a => a.user.id)).size;
    if (count === 1) {
      activityText = `${purchasedBy[0].user.name} purchased this`;
    } else if (count === 2) {
      activityText = `${purchasedBy[0].user.name} and ${purchasedBy[1].user.name} purchased this`;
    } else {
      activityText = `${purchasedBy[0].user.name} and ${count - 1} others purchased this`;
    }
    iconTypes = ['purchased'];
    badgeClass = 'purchased';
  } else if (likedBy.length > 0) {
    displayActivities = likedBy;
    const count = new Set(likedBy.map(a => a.user.id)).size;
    if (count === 1) {
      activityText = `${likedBy[0].user.name} liked this`;
    } else if (count === 2) {
      activityText = `${likedBy[0].user.name} and ${likedBy[1].user.name} liked this`;
    } else {
      activityText = `${likedBy[0].user.name} and ${count - 1} others liked this`;
    }
    iconTypes = ['liked'];
    badgeClass = '';
  } else if (cartBy.length > 0) {
    displayActivities = cartBy;
    const count = new Set(cartBy.map(a => a.user.id)).size;
    if (count === 1) {
      activityText = `${cartBy[0].user.name} added to cart`;
    } else {
      activityText = `${cartBy[0].user.name} and ${count - 1} others are interested`;
    }
    iconTypes = ['cart'];
    badgeClass = '';
  }
  
  return (
    <div className={`friends-activity-badge ${badgeClass}`}>
      <div className="friends-activity-content">
        <div className="friends-activity-avatars">
          {displayActivities.slice(0, 2).map((activity, idx) => (
            <div 
              key={`${activity.user.id}-${idx}`}
              className="friends-activity-avatar"
              style={{ zIndex: 2 - idx }}
            >
              {activity.user.profile_picture ? (
                <img src={activity.user.profile_picture} alt={activity.user.name} />
              ) : (
                <div className="friends-activity-avatar-placeholder">
                  {activity.user.name.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
          ))}
        </div>
        <div className="friends-activity-text">
          {activityText}
        </div>
      </div>
      <div className="friends-activity-icons">
        {iconTypes.map((type, idx) => (
          <div key={idx} className="friends-activity-icon">
            {type === 'purchased' && <i className="fas fa-shopping-cart"></i>}
            {type === 'liked' && <i className="fas fa-heart"></i>}
            {type === 'cart' && <i className="fas fa-shopping-bag"></i>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FriendsActivity;
