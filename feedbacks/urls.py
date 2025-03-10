from django.urls import path, include
from rest_framework.routers import DefaultRouter

from feedbacks.views import FeedbackViewSet

router = DefaultRouter()
router.register("", FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
