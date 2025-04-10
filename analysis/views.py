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

from .models import Video, EmotionAnalysis, EmotionAnalysisSummary, EmotionTimeline
from .serializers import (
    VideoSerializer, 
    VideoInitSerializer, 
    ChunkUploadSerializer,
    EmotionAnalysisSerializer,
    EmotionAnalysisSummarySerializer,
    EmotionTimelineSerializer,
    VideoDetailSerializer
)
from .tasks import analyze_video_emotions

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VideoDetailSerializer
        return self.serializer_class
    
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
        try:
            video = serializer.save()
            # Queue video for emotion analysis
            analyze_video_emotions.delay(str(video.id))
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            raise
        
    @action(detail=True, methods=['get'])
    def analysis_status(self, request, pk=None):
        """Get the analysis status of a video"""
        try:
            video = self.get_object()
            return Response({'status': video.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reanalyze(self, request, pk=None):
        """Trigger reanalysis of the video"""
        try:
            video = self.get_object()
            video.status = 'pending'
            video.save()
            
            # Clear existing analysis
            EmotionAnalysis.objects.filter(video=video).delete()
            EmotionTimeline.objects.filter(video=video).delete()
            EmotionAnalysisSummary.objects.filter(video=video).delete()
            
            # Queue video for emotion analysis
            analyze_video_emotions.delay(str(video.id))
            
            return Response({'status': 'reanalysis queued'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download_data_csv(self, request, pk=None):
        """Download emotion analysis data as CSV"""
        try:
            video = self.get_object()
            
            # Check if analysis is complete
            if video.status != 'completed':
                return Response(
                    {'error': 'Video analysis is not complete yet'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Generate CSV content
            csv_content = video.get_emotion_data_csv()
            
            # Create HTTP response with CSV file
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{video.title}_emotion_data.csv"'
            
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download_timeline_csv(self, request, pk=None):
        """Download emotion timeline as CSV"""
        try:
            video = self.get_object()
            
            # Check if analysis is complete
            if video.status != 'completed':
                return Response(
                    {'error': 'Video analysis is not complete yet'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Generate CSV content
            csv_content = video.get_emotion_timeline_csv()
            
            # Create HTTP response with CSV file
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{video.title}_emotion_timeline.csv"'
            
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmotionAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmotionAnalysisSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp']
    ordering = ['timestamp']
    
    def get_queryset(self):
        try:
            video_id = self.kwargs.get('video_pk')
            return EmotionAnalysis.objects.filter(video__id=video_id)
        except Exception as e:
            print(f"Error retrieving emotion analysis: {str(e)}")
            return EmotionAnalysis.objects.none()


class EmotionTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmotionTimelineSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['start_time']
    ordering = ['start_time']
    
    def get_queryset(self):
        try:
            video_id = self.kwargs.get('video_pk')
            return EmotionTimeline.objects.filter(video__id=video_id)
        except Exception as e:
            print(f"Error retrieving emotion timeline: {str(e)}")
            return EmotionTimeline.objects.none()


class EmotionAnalysisSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmotionAnalysisSummarySerializer
    
    def get_queryset(self):
        try:
            if 'video_pk' in self.kwargs:
                video_id = self.kwargs.get('video_pk')
                return EmotionAnalysisSummary.objects.filter(video__id=video_id)
            return EmotionAnalysisSummary.objects.all()
        except Exception as e:
            print(f"Error retrieving emotion summary: {str(e)}")
            return EmotionAnalysisSummary.objects.none()
