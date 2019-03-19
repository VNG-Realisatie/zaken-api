import json

from django.core.serializers.json import DjangoJSONEncoder

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.timezone import now

from vng_api_common.models import APICredential


NC_URL = 'http://127.0.0.1:8001/api/v1/notificaties'
KANAAL = 'zaken'
BRON_OBJECT = 'zaak'
KENMERKEN = [
    {"bron": "082096752011"},
    {"zaaktype": "example.com/api/v1/zaaktypen/5aa5c"},
    {"vertrouwelijkeidaanduiding": "openbaar"}
]


class NotificationMixin:

    def construct_message(self, data, *args, **kwargs):
        action = kwargs.get('action', 'unknown action')
        resource = kwargs.get('name', 'unknown name')

        res = {
            "kanaal": KANAAL,
            "resourceUrl": data.get('url', None),
            "resource": resource,
            "actie": action,
            "aanmaakDatum": now(),
            "kenmerken": KENMERKEN}

        if resource == BRON_OBJECT:
            res["bronUrl"] = data.get('url', None)
        else:
            res["bronUrl"] = data.get(BRON_OBJECT, None)

        # return json.dumps(res, cls=DjangoJSONEncoder)
        return res

    def notify(self, response):
        response = None
        if response.status_code >= 200 and response.status_code < 300:
            Client = import_string(settings.ZDS_CLIENT_CLASS)
            client = Client.from_url(NC_URL)
            client.auth = APICredential.get_auth(
                NC_URL,
                scopes=['notificaties.scopes.publiceren']
            )

            msg = self.construct_message(response.data, action=self.action, resource=self.basename)

            print('msg=', msg)
            response = client.request(NC_URL, 'notificaties', method='POST', data=msg)
        return response


class NotificationCreateMixin(NotificationMixin):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self.notify(response)
        return response


class NotificationUpdateMixin(NotificationMixin):
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self.notify(response.status_code, response.data)
        return response


class NotificationDestroyMixin(NotificationMixin):
    def destroy(self, request, *args, **kwargs):
        # get url via serializer
        data = self.get_serializer(self.get_object()).data

        response = super().destroy(request, *args, **kwargs)
        self.notify(response.status_code, data)
        return response


class NotificationViewSetMixin(NotificationCreateMixin,
                               NotificationUpdateMixin,
                               NotificationDestroyMixin):
    pass
