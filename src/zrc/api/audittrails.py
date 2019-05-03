from ..conf.base import SITE_TITLE
from ..datamodel.models import AuditTrail


class AuditTrailMixin:
    def create_audittrail(self, status_code, action, oud, nieuw):
        data = nieuw if nieuw else oud
        if SITE_TITLE == 'Zaak Registratie Component (ZRC)':
            bron = 'ZRC'
            hoofdObject = data['url'] if self.basename == 'zaak' else data['zaak']
        trail = AuditTrail(
            bron=bron,
            actie=action,
            actieWeergave='',
            resultaat=status_code,
            hoofdObject=hoofdObject,
            resource=self.basename,
            resourceUrl=data['url'],
            oud=oud,
            nieuw=nieuw,
        )
        trail.save()

class AuditTrailCreateMixin(AuditTrailMixin):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self.create_audittrail(
            response.status_code,
            'create',
            oud=None,
            nieuw=response.data,
        )
        return response

class AuditTrailUpdateMixin(AuditTrailMixin):
    def update(self, request, *args, **kwargs):
        oud = self.get(request, *args, **kwargs).data
        action = 'update' if request.method == 'PUT' else 'partial_update'
        response = super().update(request, *args, **kwargs)
        self.create_audittrail(
            response.status_code,
            action,
            oud=oud,
            nieuw=response.data,
        )
        return response


class AuditTrailDestroyMixin(AuditTrailMixin):
    def destroy(self, request, *args, **kwargs):
        oud = self.get(request, *args, **kwargs).data
        response = super().destroy(request, *args, **kwargs)
        self.create_audittrail(
            response.status_code,
            'delete',
            oud=oud,
            nieuw=None
        )
        return response

class AuditTrailViewsetMixin(AuditTrailCreateMixin,
                             AuditTrailUpdateMixin,
                             AuditTrailDestroyMixin):
    pass
