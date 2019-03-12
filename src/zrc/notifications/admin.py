from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import NotificationsConfig, Subscription


class SubscriptionInline(admin.TabularInline):
    model = Subscription


@admin.register(NotificationsConfig)
class NotificationsConfigAdmin(SingletonModelAdmin):
    list_display = ('location', 'subscriptions')
    inlines = [SubscriptionInline]

    def subscriptions(self, obj):
        urls = obj.exclude(subscription_set___subscription='').values_list('subscription_set___subscription')
        return ", ".join(urls)
