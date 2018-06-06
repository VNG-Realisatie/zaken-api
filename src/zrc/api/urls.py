from django.urls import path, include

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('v<int:version>/', include(router.urls)),
]
