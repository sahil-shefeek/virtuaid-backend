from django.urls import include, path
from rest_framework.routers import DefaultRouter

from associates.views import AssociateViewSet

router = DefaultRouter()
router.register('', AssociateViewSet)
urlpatterns = [
    path('', include(router.urls)),
]