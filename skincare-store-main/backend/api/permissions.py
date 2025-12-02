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
