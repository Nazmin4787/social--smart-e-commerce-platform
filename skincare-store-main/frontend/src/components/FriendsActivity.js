import React from 'react';

const FriendsActivity = ({ activities }) => {
  console.log('FriendsActivity component - activities:', activities);
  
  if (!activities || activities.length === 0) {
    console.log('FriendsActivity - No activities to display');
    return null;
  }

  console.log('FriendsActivity - Displaying', activities.length, 'activities');

  // Get the most recent activity
  const recentActivity = activities[0];
  
  // If there are multiple friends, show count
  const friendsCount = new Set(activities.map(a => a.user.id)).size;
  
  return (
    <div className="friends-activity-badge">
      <div className="friends-activity-content">
        <div className="friends-activity-avatars">
          {activities.slice(0, 2).map((activity, index) => (
            <div 
              key={activity.user.id} 
              className="friends-activity-avatar"
              style={{ zIndex: 2 - index }}
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
          {friendsCount === 1 ? (
            <>
              <span className="friends-activity-name">{recentActivity.user.name}</span>
              {' '}
              <span className="friends-activity-action">
                {recentActivity.type === 'liked' ? 'liked this' : 'added to cart'}
              </span>
            </>
          ) : friendsCount === 2 ? (
            <>
              <span className="friends-activity-name">
                {activities[0].user.name}
              </span>
              {' and '}
              <span className="friends-activity-name">
                {activities[1].user.name}
              </span>
              {' '}
              <span className="friends-activity-action">
                {recentActivity.type === 'liked' ? 'liked this' : 'are interested'}
              </span>
            </>
          ) : (
            <>
              <span className="friends-activity-name">
                {activities[0].user.name}
              </span>
              {' and '}
              <span className="friends-activity-count">
                {friendsCount - 1} others
              </span>
              {' '}
              <span className="friends-activity-action">are interested</span>
            </>
          )}
        </div>
      </div>
      <div className="friends-activity-icon">
        {recentActivity.type === 'liked' ? (
          <i className="fas fa-heart"></i>
        ) : (
          <i className="fas fa-shopping-bag"></i>
        )}
      </div>
    </div>
  );
};

export default FriendsActivity;
