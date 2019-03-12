from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from vng_api_common.permissions import ScopesRequired

from .serializers import NotificatieSerializer
from .scopes import SCOPE_NOTIFICATIES_STUREN


class NotificationView(APIView):
    """
    View to receive webhooks
    """
    swagger_schema = None

    permission_classes = (ScopesRequired,)
    required_scopes = SCOPE_NOTIFICATIES_STUREN

    def post(self, request, *args, **kwargs):
        serializer = NotificatieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: actually do something with the notifications
        return Response(status=status.HTTP_200_OK)
