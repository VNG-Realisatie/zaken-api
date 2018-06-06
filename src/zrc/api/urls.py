from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .viewsets import ZaakViewSet, StatusViewSet

router = DefaultRouter()
router.register('zaken', ZaakViewSet)
router.register('statussen', StatusViewSet)

urlpatterns = [
    path('v<int:version>/', include(router.urls)),
]
