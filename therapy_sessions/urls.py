from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from therapy_sessions.views import SessionViewSet, SessionVideosView

router = DefaultRouter()
router.register('', SessionViewSet, basename='sessions')

# Add nested route for session videos
session_router = routers.NestedSimpleRouter(router, r'', lookup='session')

urlpatterns = [
    path('', include(router.urls)),
    # Add path for emotion analysis
    path('<int:session_pk>/analysis/emotions/', SessionVideosView.as_view(), name='session-emotion-analysis'),
]
