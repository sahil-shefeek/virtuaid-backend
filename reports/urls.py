from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reports.views import ReportsViewSet

router = DefaultRouter()
router.register("", ReportsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
