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
from drf_spectacular.utils import (
    extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample,
    OpenApiResponse
)
from drf_spectacular.openapi import AutoSchema

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
from .tasks import analyze_video_emotions  # Temporarily commented out

@extend_schema_view(
    list=extend_schema(
        summary="List therapy session videos",
        description="Retrieve a paginated list of therapy session videos with "
                   "filtering and search capabilities. Videos are filtered "
                   "based on user permissions and role-based access control.",
        tags=["Video Analysis"],
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search videos by title or description',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample(
                        'Search by title',
                        value='CBT Session',
                        description='Find videos with "CBT Session" in title'
                    ),
                    OpenApiExample(
                        'Search by description',
                        value='anxiety management',
                        description='Find videos about anxiety management'
                    )
                ]
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample(
                        'Order by upload date (newest first)',
                        value='-uploaded_at',
                        description='Sort by upload date descending'
                    ),
                    OpenApiExample(
                        'Order by title alphabetically',
                        value='title',
                        description='Sort by title A-Z'
                    )
                ]
            )
        ],
        examples=[
            OpenApiExample(
                "Video List Response",
                summary="List of therapy session videos",
                description="Example response showing paginated video list",
                value={
                    "count": 25,
                    "next": "http://api.example.com/videos/?page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "CBT Session - Week 1",
                            "description": "Initial cognitive behavioral therapy session",
                            "file": "/media/videos/cbt_week1.mp4",
                            "file_size": 52428800,
                            "status": "completed",
                            "uploaded_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:45:00Z",
                            "therapy_session": 1,
                            "resident": 1
                        }
                    ]
                },
                response_only=True
            )
        ]
    ),
    create=extend_schema(
        summary="Upload a new therapy session video",
        description="Upload a new video file for emotion analysis. The video "
                   "will be automatically queued for AI-powered emotion "
                   "analysis upon successful upload.",
        tags=["Video Analysis"],
        examples=[
            OpenApiExample(
                "Video Upload Request",
                summary="Basic video upload",
                description="Upload video with title and optional metadata",
                value={
                    "title": "Group Therapy Session",
                    "description": "Multi-patient therapy session recording",
                    "therapy_session": 2,
                    "resident": 3
                },
                request_only=True
            ),
            OpenApiExample(
                "Video Upload Response",
                summary="Successful upload response",
                description="Response after successful video upload",
                value={
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "title": "Group Therapy Session",
                    "description": "Multi-patient therapy session recording",
                    "file": "/media/videos/group_therapy_002.mp4",
                    "file_size": 104857600,
                    "status": "pending",
                    "uploaded_at": "2024-01-15T14:20:00Z",
                    "updated_at": "2024-01-15T14:20:00Z",
                    "therapy_session": 2,
                    "resident": 3
                },
                response_only=True
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Get detailed video information",
        description="Retrieve comprehensive video details including embedded "
                   "emotion analysis summary and processing status.",
        tags=["Video Analysis"],
        examples=[
            OpenApiExample(
                "Complete Video Details",
                summary="Video with analysis results",
                description="Detailed video view including emotion analysis",
                value={
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "CBT Session - Week 1",
                    "description": "Initial cognitive behavioral therapy session",
                    "file": "/media/videos/cbt_week1.mp4",
                    "file_size": 52428800,
                    "uploaded_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:45:00Z",
                    "status": "completed",
                    "therapy_session": 1,
                    "resident": 1,
                    "emotion_summary": {
                        "id": 1,
                        "video": "550e8400-e29b-41d4-a716-446655440000",
                        "angry_avg": 0.12,
                        "sad_avg": 0.25,
                        "happy_avg": 0.63,
                        "dominant_emotion": "happy",
                        "emotion_counts": {
                            "happy": 1250,
                            "sad": 480,
                            "angry": 200,
                            "total_frames": 1930
                        }
                    }
                },
                response_only=True
            )
        ]
    ),
    update=extend_schema(
        summary="Update video metadata",
        description="Update video title, description, and linked therapy "
                   "session or resident information.",
        tags=["Video Analysis"]
    ),
    partial_update=extend_schema(
        summary="Partially update video metadata",
        description="Update specific video fields without affecting others.",
        tags=["Video Analysis"]
    ),
    destroy=extend_schema(
        summary="Delete video and analysis data",
        description="Permanently delete video file and all associated "
                   "emotion analysis data. This action cannot be undone.",
        tags=["Video Analysis"]
    )
)
class VideoViewSet(viewsets.ModelViewSet):
    """
    Video management ViewSet for therapy session recordings.
    
    This ViewSet provides comprehensive video management capabilities for 
    therapy session recordings with integrated emotion analysis. Videos are
    automatically queued for AI-powered emotion analysis upon upload.
    
    Key features:
    - Role-based access control (superadmin, admin, manager)
    - Automatic emotion analysis pipeline integration
    - Search and filtering capabilities
    - Comprehensive metadata management
    - Processing status tracking
    
    Video processing workflow:
    1. Upload video with metadata
    2. Automatic analysis queue registration
    3. AI emotion detection processing
    4. Results aggregation and summary generation
    5. Analysis data availability via custom actions
    
    Permissions:
    - Superadmin: Access to all videos across the platform
    - Admin: Access to videos from their managed care homes
    - Manager: Access to videos from care homes they manage
    """
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
        
    @extend_schema(
        summary="Get video analysis status",
        description="Retrieve the current emotion analysis processing status "
                   "for a specific video. Status values include: pending, "
                   "processing, completed, failed.",
        tags=["Video Analysis"],
        responses={
            200: OpenApiResponse(
                description="Analysis status retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Analysis Complete",
                        summary="Video analysis completed",
                        description="Video has finished emotion analysis",
                        value={"status": "completed"}
                    ),
                    OpenApiExample(
                        "Analysis In Progress",
                        summary="Video analysis in progress",
                        description="Video is currently being processed",
                        value={"status": "processing"}
                    ),
                    OpenApiExample(
                        "Analysis Pending",
                        summary="Video analysis queued",
                        description="Video is queued for analysis",
                        value={"status": "pending"}
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Server error during status retrieval",
                examples=[
                    OpenApiExample(
                        "Server Error",
                        summary="Internal server error",
                        description="Error occurred while checking status",
                        value={"error": "Database connection failed"}
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['get'])
    def analysis_status(self, request, pk=None):
        """Get the analysis status of a video"""
        try:
            video = self.get_object()
            return Response({'status': video.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="Trigger video reanalysis",
        description="Restart the emotion analysis process for a video. This "
                   "clears all existing analysis data and queues the video "
                   "for fresh emotion analysis processing.",
        tags=["Video Analysis"],
        responses={
            200: OpenApiResponse(
                description="Reanalysis successfully queued",
                examples=[
                    OpenApiExample(
                        "Reanalysis Queued",
                        summary="Successfully started reanalysis",
                        description="Video has been queued for reanalysis",
                        value={"status": "reanalysis queued"}
                    )
                ]
            ),
            500: OpenApiResponse(
                description="Server error during reanalysis setup",
                examples=[
                    OpenApiExample(
                        "Reanalysis Error",
                        summary="Failed to queue reanalysis",
                        description="Error occurred while setting up reanalysis",
                        value={"error": "Failed to clear existing analysis data"}
                    )
                ]
            )
        }
    )
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
    
    @extend_schema(
        summary="Get emotion analysis frames",
        description="Retrieve detailed emotion analysis data for each "
                   "analyzed frame in the video, ordered chronologically "
                   "by timestamp.",
        tags=["Video Analysis"],
        responses={
            200: OpenApiResponse(
                description="Emotion frames retrieved successfully",
                examples=[
                    OpenApiExample(
                        "Emotion Frames Data",
                        summary="List of analyzed video frames",
                        description="Frame-by-frame emotion analysis results",
                        value=[
                            {
                                "id": 1,
                                "video": "550e8400-e29b-41d4-a716-446655440000",
                                "timestamp": 15.5,
                                "angry": 0.02,
                                "sad": 0.1,
                                "happy": 0.88,
                                "dominant_emotion": "happy",
                                "created_at": "2024-01-15T10:35:00Z"
                            },
                            {
                                "id": 2,
                                "video": "550e8400-e29b-41d4-a716-446655440000",
                                "timestamp": 16.0,
                                "angry": 0.05,
                                "sad": 0.15,
                                "happy": 0.80,
                                "dominant_emotion": "happy",
                                "created_at": "2024-01-15T10:35:05Z"
                            }
                        ]
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['get'], url_path='frames')
    def emotion_frames(self, request, pk=None):
        """Get emotion analysis frames for this video"""
        try:
            video = self.get_object()
            frames = EmotionAnalysis.objects.filter(
                video=video
            ).order_by('timestamp')
            serializer = EmotionAnalysisSerializer(frames, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get emotion timeline",
        description="Retrieve emotion timeline segments showing periods of "
                   "consistent emotional states throughout the video.",
        tags=["Video Analysis"],
        responses={
            200: OpenApiResponse(
                description="Emotion timeline retrieved successfully"
            )
        }
    )
    @action(detail=True, methods=['get'], url_path='timeline')
    def emotion_timeline(self, request, pk=None):
        """Get emotion timeline for this video"""
        try:
            video = self.get_object()
            timeline = EmotionTimeline.objects.filter(
                video=video
            ).order_by('start_time')
            serializer = EmotionTimelineSerializer(timeline, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get emotion analysis summary",
        description=(
            "Retrieve the comprehensive emotion analysis summary for this "
            "video. Provides aggregated statistics, insights, and key "
            "findings from the emotion detection analysis.\n\n"
            "Summary Includes:\n"
            "- Overall emotion distribution\n"
            "- Peak emotional moments\n"
            "- Session quality metrics\n"
            "- Therapeutic insights\n\n"
            "Business Value:\n"
            "- Quick session overview for therapists\n"
            "- Progress tracking capabilities\n"
            "- Data-driven therapy adjustments"
        ),
        tags=["Video Analysis"],
        responses={
            200: OpenApiResponse(
                description="Emotion analysis summary",
                response=EmotionAnalysisSummarySerializer,
                examples=[
                    OpenApiExample(
                        "Complete summary",
                        value={
                            "id": 1,
                            "video": 15,
                            "dominant_emotion": "calm",
                            "emotion_counts": {
                                "happy": 45,
                                "calm": 78,
                                "engaged": 32,
                                "frustrated": 12
                            },
                            "average_confidence": 0.87,
                            "session_quality_score": 8.3,
                            "total_frames_analyzed": 1890,
                            "analysis_duration": "00:03:15",
                            "created_at": "2025-09-03T10:30:00Z"
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="Summary not found"),
            500: OpenApiResponse(description="Server error")
        }
    )
    @action(detail=True, methods=['get'], url_path='summary')
    def emotion_summary(self, request, pk=None):
        """Get emotion analysis summary for this video"""
        try:
            video = self.get_object()
            summary = EmotionAnalysisSummary.objects.filter(video=video).first()
            if summary:
                serializer = EmotionAnalysisSummarySerializer(summary)
                return Response(serializer.data)
            else:
                return Response(
                    {'message': 'No summary available'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Download emotion analysis data as CSV",
        description=(
            "Download detailed emotion analysis data for this video as a "
            "CSV file. Includes frame-by-frame emotion detection results "
            "with timestamps, confidence scores, and detected emotions.\n\n"
            "CSV Contents:\n"
            "- Frame number and timestamp\n"
            "- Detected emotions with confidence scores\n"
            "- Facial landmarks data\n"
            "- Processing metadata\n\n"
            "Requirements:\n"
            "- Video analysis must be completed\n"
            "- User must have access to the video"
        ),
        tags=["Video Analysis"],
        responses={
            200: OpenApiResponse(
                description="CSV file download",
                response=str,
                examples=[
                    OpenApiExample(
                        "CSV file response",
                        value="attachment; filename=\"emotion_data.csv\"",
                        description="CSV file with emotion analysis data"
                    )
                ]
            ),
            400: OpenApiResponse(description="Video analysis not complete"),
            404: OpenApiResponse(description="Video not found"),
            500: OpenApiResponse(description="Server error")
        }
    )
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
            response['Content-Disposition'] = (
                f'attachment; filename="{video.title}_emotion_data.csv"'
            )

            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Download emotion timeline as CSV",
        description=(
            "Download emotion timeline data for this video as a CSV file. "
            "Provides aggregated emotion data over time intervals, showing "
            "how emotions change throughout the therapy session.\n\n"
            "CSV Contents:\n"
            "- Time intervals (start/end timestamps)\n"
            "- Dominant emotion per interval\n"
            "- Emotion intensity scores\n"
            "- Statistical summaries\n\n"
            "Use Cases:\n"
            "- Progress tracking over sessions\n"
            "- Identifying emotional patterns\n"
            "- Research and reporting"
        ),
        tags=["Video Analysis"],
        responses={
            200: OpenApiResponse(
                description="CSV file download",
                response=str,
                examples=[
                    OpenApiExample(
                        "CSV timeline response",
                        value="attachment; filename=\"timeline.csv\"",
                        description="CSV file with emotion timeline data"
                    )
                ]
            ),
            400: OpenApiResponse(description="Video analysis not complete"),
            404: OpenApiResponse(description="Video not found"),
            500: OpenApiResponse(description="Server error")
        }
    )
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
            response['Content-Disposition'] = (
                f'attachment; filename="{video.title}_emotion_timeline.csv"'
            )

            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


