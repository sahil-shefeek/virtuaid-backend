import os
import uuid
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, permissions, parsers, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import Video, EmotionAnalysis, EmotionAnalysisSummary
from .serializers import (
    VideoSerializer, 
    VideoInitSerializer, 
    ChunkUploadSerializer,
    EmotionAnalysisSerializer,
    EmotionAnalysisSummarySerializer
)
from .tasks import analyze_video_emotions

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title']
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_superadmin:
            if user.is_admin:
                queryset = queryset.filter(therapy_session__resident__care_home__admin=user)
            elif user.is_manager:
                # Get care homes managed by this manager
                from carehome_managers.models import CarehomeManagers
                managed_carehomes = CarehomeManagers.objects.filter(manager=user).values_list('carehome', flat=True)
                queryset = queryset.filter(therapy_session__resident__care_home__id__in=managed_carehomes)
        
        return queryset
    
    def perform_create(self, serializer):
        video = serializer.save()
        # Queue video for emotion analysis
        analyze_video_emotions.delay(str(video.id))
        
    @action(detail=True, methods=['get'])
    def analysis_status(self, request, pk=None):
        """Get the analysis status of a video"""
        video = self.get_object()
        return Response({'status': video.status})
    
    @action(detail=True, methods=['post'])
    def reanalyze(self, request, pk=None):
        """Trigger reanalysis of the video"""
        video = self.get_object()
        video.status = 'pending'
        video.save()
        
        # Clear existing analysis
        EmotionAnalysis.objects.filter(video=video).delete()
        EmotionAnalysisSummary.objects.filter(video=video).delete()
        
        # Queue video for emotion analysis
        analyze_video_emotions.delay(str(video.id))
        
        return Response({'status': 'reanalysis queued'})

class EmotionAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmotionAnalysisSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp']
    ordering = ['timestamp']
    
    def get_queryset(self):
        video_id = self.kwargs.get('video_pk')
        return EmotionAnalysis.objects.filter(video__id=video_id)

class EmotionAnalysisSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmotionAnalysisSummarySerializer
    
    def get_queryset(self):
        if 'video_pk' in self.kwargs:
            video_id = self.kwargs.get('video_pk')
            return EmotionAnalysisSummary.objects.filter(video__id=video_id)
        return EmotionAnalysisSummary.objects.all()
