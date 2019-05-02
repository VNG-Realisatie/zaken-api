from ..datamodel.models import AuditTrail
from ..conf.base import SITE_TITLE

class AuditTrailMixin:
    def create_audittrail(self, status_code, action, data, **kwargs):
        # import ipdb; ipdb.set_trace()
        if SITE_TITLE == 'Zaak Registratie Component (ZRC)':
            bron = 'ZRC'
            if self.basename == 'zaak':
                hoofdObject = data['url']
            else:
                hoofdObject = data['zaak']
        trail = AuditTrail(
            bron=bron,
            actie=action,
            actieWeergave='',
            resultaat=status_code,
            hoofdObject=hoofdObject,
            resource=self.basename,
            resourceUrl=data['url'],
        )
        trail.save()

class AuditTrailCreateMixin(AuditTrailMixin):
    def create(self, request, *args, **kwargs):
        # import ipdb; ipdb.set_trace()
        response = super().create(request, *args, **kwargs)
        self.create_audittrail(response.status_code, 'create', response.data)
        return response

class AuditTrailUpdateMixin(AuditTrailMixin):
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self.create_audittrail(response.status_code, 'update', response.data)
        return response

class AuditTrailPartialUpdateMixin(AuditTrailMixin):
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        self.create_audittrail(response.status_code, 'partial_update', response.data)
        return response

class AuditTrailDestroyMixin(AuditTrailMixin):
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        self.create_audittrail(response.status_code, 'delete', response.data)
        return response

class AuditTrailViewsetMixin(AuditTrailCreateMixin,
                             AuditTrailUpdateMixin,
                             AuditTrailPartialUpdateMixin,
                             AuditTrailDestroyMixin):
    pass
