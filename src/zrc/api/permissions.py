from rest_framework import permissions
from rest_framework.request import Request


class ZaaktypePermission(permissions.BasePermission):
    """
    Object-level permissions based on the zaaktypes claim.
    """

    def has_object_permission(self, request: Request, view, obj) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        zaaktypes = request.jwt_payload.get('zaaktypes', [])
        return obj.zaaktype in zaaktypes
