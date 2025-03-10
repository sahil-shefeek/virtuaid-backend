from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CareHomeViewSet

# from .views import CareHomeDetailAPIView, CareHomeListCreateAPIView, CareHomeCreateAPIView

carehome_router = DefaultRouter()

carehome_router.register('', CareHomeViewSet, basename='carehomes')


urlpatterns = [
    path('', include(carehome_router.urls)),
]
