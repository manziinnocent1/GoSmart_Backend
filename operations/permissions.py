from rest_framework.permissions import BasePermission


class IsStaffAdmin(BasePermission):
    message = "Administrator access is required."

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.is_staff
            and request.user.role == "admin"
        )
