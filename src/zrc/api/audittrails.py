from django.db import transaction

from ..datamodel.models import AuditTrail


class AuditTrailMixin:
    audit = None

    def get_audittrail_main_object_url(self, data, main_resource):
        return data[main_resource]

    def create_audittrail(self, status_code, action, version_before_edit, version_after_edit):
        data = version_after_edit if version_after_edit else version_before_edit
        if self.basename == self.audit.main_resource:
            main_object = data['url']
        else:
            main_object = self.get_audittrail_main_object_url(data, self.audit.main_resource)

        trail = AuditTrail(
            bron=self.audit.component_name,
            actie=action,
            actieWeergave='',
            resultaat=status_code,
            hoofdObject=main_object,
            resource=self.basename,
            resourceUrl=data['url'],
            oud=version_before_edit,
            nieuw=version_after_edit,
        )
        trail.save()

    def destroy_related_audittrails(self, main_object_url):
        AuditTrail.objects.filter(hoofdObject=main_object_url).delete()


class AuditTrailCreateMixin(AuditTrailMixin):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self.create_audittrail(
            response.status_code,
            'create',
            version_before_edit=None,
            version_after_edit=response.data,
        )
        return response


class AuditTrailUpdateMixin(AuditTrailMixin):
    def update(self, request, *args, **kwargs):
        version_before_edit = self.get(request, *args, **kwargs).data
        action = 'update' if request.method == 'PUT' else 'partial_update'
        response = super().update(request, *args, **kwargs)
        self.create_audittrail(
            response.status_code,
            action,
            version_before_edit=version_before_edit,
            version_after_edit=response.data,
        )
        return response


class AuditTrailDestroyMixin(AuditTrailMixin):
    def destroy(self, request, *args, **kwargs):
        version_before_edit = self.get(request, *args, **kwargs).data
        if self.basename == self.audit.main_resource:
            with transaction.atomic():
                response = super().destroy(request, *args, **kwargs)
                self.destroy_related_audittrails(version_before_edit['url'])
                return response
        else:
            response = super().destroy(request, *args, **kwargs)
            self.create_audittrail(
                response.status_code,
                'delete',
                version_before_edit=version_before_edit,
                version_after_edit=None
            )
            return response

class AuditTrailViewsetMixin(AuditTrailCreateMixin,
                             AuditTrailUpdateMixin,
                             AuditTrailDestroyMixin):
    pass
