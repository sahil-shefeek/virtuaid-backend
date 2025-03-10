from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarehomeManagerViewSet

# from .views import CareHomeDetailAPIView, CareHomeListCreateAPIView, CareHomeCreateAPIView


carehome_manager_router = DefaultRouter()
carehome_manager_router.register('', CarehomeManagerViewSet)

urlpatterns = [
    path('', include(carehome_manager_router.urls)),
]
