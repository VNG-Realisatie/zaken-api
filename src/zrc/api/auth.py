from django.conf import settings

from zds_client import ClientAuth

ztc_auth = ClientAuth(
    client_id=settings.ZTC_JWT_CLIENT_ID,
    secret=settings.ZTC_JWT_SECRET,
    scopes=['zds.scopes.zaaktypes.lezen']
)
