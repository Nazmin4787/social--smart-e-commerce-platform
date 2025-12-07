from .utils import decode_jwt
from .models import AppUser


class IsAdminUser:
    """Simple permission class used by views to check admin access.

    Usage:
        perm = IsAdminUser()
        if not perm.has_permission(request):
            return JsonResponse({'error': 'Forbidden'}, status=403)

    This mirrors Django REST Framework's `IsAdminUser` concept but is
    tailored to the project's custom JWT + `AppUser` model.
    """

    def has_permission(self, request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return False
        data = decode_jwt(token)
        if not data or "error" in data:
            return False
        try:
            user = AppUser.objects.get(pk=data.get('user_id'))
        except AppUser.DoesNotExist:
            return False
        return bool(getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False))

    def get_user(self, request):
        """Return the AppUser instance for the current request, or None."""
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return None
        data = decode_jwt(token)
        if not data or "error" in data:
            return None
        try:
            return AppUser.objects.get(pk=data.get('user_id'))
        except AppUser.DoesNotExist:
            return None


class IsRegularUser:
    """Permission class to check if user is a regular user (not admin).

    Usage:
        perm = IsRegularUser()
        if not perm.has_permission(request):
            return JsonResponse({'error': 'This action is only available to regular users'}, status=403)
    """

    def has_permission(self, request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            print("DEBUG: No token found")
            return False
        data = decode_jwt(token)
        if not data or "error" in data:
            print(f"DEBUG: JWT decode failed: {data}")
            return False
        try:
            user = AppUser.objects.get(pk=data.get('user_id'))
            print(f"DEBUG: User {user.id} ({user.email}), is_staff={user.is_staff}, is_superuser={user.is_superuser}")
            # Regular user: not staff and not superuser
            is_regular = not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False))
            print(f"DEBUG: Is regular user: {is_regular}")
            return is_regular
        except AppUser.DoesNotExist:
            print("DEBUG: User does not exist")
            return False

    def get_user(self, request):
        """Return the AppUser instance for the current request, or None."""
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return None
        data = decode_jwt(token)
        if not data or "error" in data:
            return None
        try:
            return AppUser.objects.get(pk=data.get('user_id'))
        except AppUser.DoesNotExist:
            return None
