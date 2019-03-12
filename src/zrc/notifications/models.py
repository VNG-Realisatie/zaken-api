from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from solo.models import SingletonModel


class NotificationsConfig(SingletonModel):
    location = models.URLField(_("location"), help_text=_("API Root of the NC to use"))

    class Meta:
        verbose_name = _("Notificatiescomponentconfiguratie")

    def __str__(self):
        return self.location


class Subscription(models.Model):
    """
    A single subscription.
    """
    config = models.ForeignKey('NotificationsConfig', on_delete=models.CASCADE)

    callback_url = models.URLField(
        _("callback url"),
        help_text=_("Where to send the notifications (webhook url)")
    )
    client_id = models.CharField(
        _("client ID"), max_length=50,
        help_text=_("Client ID to construct the auth token")
    )
    secret = models.CharField(
        _("client secret"), max_length=50,
        help_text=_("Secret to construct the auth token")
    )
    channels = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_("channels"),
        help_text=_("Comma-separated list of channels to subscribe to")
    )

    _subscription = models.URLField(
        _("NC subscription"), blank=True, editable=False,
        help_text=_("Subscription as it is known in the NC")
    )

    class Meta:
        verbose_name = _("Webhook subscription")
        verbose_name_plural = _("Webhook subscriptions")

    def __str__(self):
        return f"{', '.join(self.channels)} - {self.callback_url}"
