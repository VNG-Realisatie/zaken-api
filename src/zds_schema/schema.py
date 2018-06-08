from drf_yasg.inspectors import SwaggerAutoSchema


class AutoSchema(SwaggerAutoSchema):

    @property
    def model(self):
        qs = self.view.get_queryset()
        return qs.model

    def get_operation_id(self, operation_keys):
        """
        Simply return the model name as lowercase string, postfixed with the operation name.
        """
        action = operation_keys[-1]
        model_name = self.model._meta.model_name
        return f"{model_name}_{action}"

    def get_tags(self, operation_keys):
        keys = operation_keys[:]

        # Similar to the operation ID, we want to group by one level deeper than catalog. Otherwise everything will be
        # under the Catalog group.
        if len(keys) > 2:
            keys = keys[1:]
        return super().get_tags(keys)
