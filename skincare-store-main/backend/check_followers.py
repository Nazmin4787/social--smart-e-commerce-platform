import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare_backend.settings')
django.setup()

from api.models import AppUser, UserFollow

# Check user 6 (Nazmin ansari)
user = AppUser.objects.get(id=6)
print(f'User: {user.name} ({user.email})')
print(f'Followers count: {user.followers.count()}')
print(f'Following count: {user.following.count()}')

print('\nFollowers (people following Nazmin):')
for follow_rel in user.followers.all():
    print(f'  - {follow_rel.follower.name} (ID: {follow_rel.follower.id})')

print('\nFollowing (people Nazmin follows):')
for follow_rel in user.following.all():
    print(f'  - {follow_rel.following.name} (ID: {follow_rel.following.id})')

print('\nAll follow relationships:')
all_follows = UserFollow.objects.all()
for f in all_follows:
    print(f'{f.follower.name} follows {f.following.name}')
