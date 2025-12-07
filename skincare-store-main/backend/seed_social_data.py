import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare_backend.settings')
django.setup()

from api.models import AppUser, UserFollow, Notification
import random

print("Starting social data seeding...")

# Get all users
users = list(AppUser.objects.all())

if len(users) < 2:
    print("Not enough users to create social relationships. Please create more users first.")
    exit()

print(f"Found {len(users)} users")

# Clear existing social data
UserFollow.objects.all().delete()
Notification.objects.all().delete()
print("Cleared existing social data")

# Create follow relationships
follow_count = 0
notification_count = 0

for user in users:
    # Each user will follow 2-5 random other users
    num_to_follow = random.randint(2, min(5, len(users) - 1))
    
    # Get random users to follow (excluding self)
    potential_follows = [u for u in users if u.id != user.id]
    users_to_follow = random.sample(potential_follows, num_to_follow)
    
    for followed_user in users_to_follow:
        # Check if already following
        if not UserFollow.objects.filter(follower=user, following=followed_user).exists():
            # Create follow relationship
            UserFollow.objects.create(
                follower=user,
                following=followed_user
            )
            follow_count += 1
            
            # Create notification
            Notification.objects.create(
                user=followed_user,
                actor=user,
                notification_type='follow',
                message=f'{user.name} started following you'
            )
            notification_count += 1

print(f"\nCreated {follow_count} follow relationships")
print(f"Created {notification_count} notifications")

# Display some statistics
print("\n=== User Social Stats ===")
for user in users[:5]:  # Show first 5 users
    followers = user.get_followers_count()
    following = user.get_following_count()
    print(f"{user.name}: {followers} followers, {following} following")

print("\n✅ Social data seeding complete!")
