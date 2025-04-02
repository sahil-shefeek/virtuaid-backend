from django.urls import include, path
from rest_framework.routers import DefaultRouter

from residents.views import ResidentViewSet

router = DefaultRouter()
router.register('', ResidentViewSet, basename='residents')
urlpatterns = [
    path('', include(router.urls)),
]