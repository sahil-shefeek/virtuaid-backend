from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    VideoViewSet, 
    EmotionAnalysisViewSet, 
    EmotionAnalysisSummaryViewSet,
    EmotionTimelineViewSet
)

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='videos')

# Nested routes for emotion analysis
video_router = routers.NestedSimpleRouter(router, r'videos', lookup='video')
video_router.register(r'frames', EmotionAnalysisViewSet, basename='video-analyses')
video_router.register(r'summary', EmotionAnalysisSummaryViewSet, basename='video-summary')
video_router.register(r'timeline', EmotionTimelineViewSet, basename='video-timeline')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(video_router.urls)),
]
