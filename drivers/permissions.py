from rest_framework.permissions import BasePermission


class IsDriver(BasePermission):
    message = "An approved driver account is required."

    def has_permission(self, request, view):
        profile = getattr(request.user, "driver_profile", None)
        return bool(
            request.user.is_authenticated
            and request.user.role == "driver"
            and profile
            and profile.approval_status == "approved"
        )


class IsDriverAccount(BasePermission):
    message = "A driver account is required."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.role == "driver"
            and hasattr(request.user, "driver_profile")
        )
