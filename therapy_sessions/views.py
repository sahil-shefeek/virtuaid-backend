from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes

from analysis.models import Video
from analysis.serializers import VideoSerializer

from .models import TherapySession
from .serializers import SessionCreateUpdateSerializer, SessionSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List therapy sessions",
        description=(
            "Retrieve a list of therapy sessions with comprehensive filtering "
            "and search capabilities.\n\n"
            "Available Filters:\n"
            "- Status-based filtering (completed, scheduled, in_progress, "
            "cancelled)\n"
            "- Category filtering (upcoming, past_due, today)\n"
            "- Feedback status filtering (completed, pending)\n"
            "- Resident-specific filtering\n"
            "- Search by resident name or session notes\n\n"
            "Ordering Options:\n"
            "- scheduled_date, created_at, updated_at"
        ),
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by session status',
                examples=[
                    OpenApiExample(
                        'Completed Sessions',
                        value='completed',
                        description='Show only completed sessions'
                    ),
                    OpenApiExample(
                        'Scheduled Sessions',
                        value='scheduled',
                        description='Show only scheduled sessions'
                    ),
                ],
                enum=['scheduled', 'in_progress', 'completed', 'cancelled'],
            ),
            OpenApiParameter(
                name='status_category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by session category',
                examples=[
                    OpenApiExample(
                        'Upcoming Sessions',
                        value='upcoming',
                        description='Future scheduled sessions'
                    ),
                    OpenApiExample(
                        'Today Sessions',
                        value='today',
                        description='Sessions scheduled for today'
                    ),
                ],
                enum=['completed', 'upcoming', 'past_due', 'in_progress', 'today'],
            ),
            OpenApiParameter(
                name='feedback_status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by feedback completion status',
                examples=[
                    OpenApiExample(
                        'Pending Feedback',
                        value='pending',
                        description='Completed sessions without feedback'
                    ),
                ],
                enum=['completed', 'pending'],
            ),
            OpenApiParameter(
                name='resident',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter sessions by resident UUID',
                examples=[
                    OpenApiExample(
                        'Resident Filter',
                        value='123e4567-e89b-12d3-a456-426614174000',
                        description='Show sessions for specific resident'
                    ),
                ],
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in resident names and session notes',
                examples=[
                    OpenApiExample(
                        'Search Example',
                        value='relaxation',
                        description='Search for sessions with "relaxation"'
                    ),
                ],
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order results by field (prefix with - for desc)',
                examples=[
                    OpenApiExample(
                        'Order by Date',
                        value='-scheduled_date',
                        description='Order by scheduled date (newest first)'
                    ),
                ],
            ),
        ],
        tags=["Therapy Sessions"],
        examples=[
            OpenApiExample(
                'Sessions List Response',
                description='Sample response showing therapy sessions',
                value={
                    "count": 12,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            'id': '123e4567-e89b-12d3-a456-426614174000',
                            'title': 'Morning VR Relaxation Session',
                            'description': 'Calming virtual environment session',
                            'resident': '456e7890-e89b-12d3-a456-426614174001',
                            'scheduled_date': '2024-09-03T10:00:00Z',
                            'duration': 30,
                            'status': 'completed',
                            'feedback_status': 'Completed'
                        }
                    ]
                },
                response_only=True
            ),
        ]
    ),
    create=extend_schema(
        summary="Schedule new therapy session",
        description=(
            "Create a new therapy session for a resident.\n\n"
            "Required Information:\n"
            "- title: Descriptive session name\n"
            "- resident: Resident UUID reference\n"
            "- scheduled_date: Session timing\n"
            "- duration: Session length in minutes\n\n"
            "Business Rules:\n"
            "- Sessions are created with 'scheduled' status by default\n"
            "- Scheduled time must be in the future\n"
            "- Duration must be between 15-120 minutes\n"
            "- User must have access to the resident's care home"
        ),
        request=SessionCreateUpdateSerializer,
        responses={201: SessionSerializer},
        tags=["Therapy Sessions"]
    ),
    retrieve=extend_schema(
        summary="Get therapy session details",
        description=(
            "Retrieve detailed information about a specific therapy session.\n\n"
            "Includes complete resident information, session status, "
            "feedback status, and all session metadata."
        ),
        tags=["Therapy Sessions"]
    ),
    update=extend_schema(
        summary="Update therapy session",
        description=(
            "Update all fields of a therapy session.\n\n"
            "Common Update Scenarios:\n"
            "- Reschedule session timing\n"
            "- Update session description or notes\n"
            "- Modify session duration\n\n"
            "Restrictions:\n"
            "- Cannot update completed sessions\n"
            "- User must have access to the resident's care home"
        ),
        tags=["Therapy Sessions"]
    ),
    partial_update=extend_schema(
        summary="Partially update therapy session",
        description=(
            "Update specific fields of a therapy session.\n\n"
            "Common Use Cases:\n"
            "- Change session status\n"
            "- Add session notes\n"
            "- Update timing information\n\n"
            "NOTE: Use specific action endpoints for status changes "
            "when available (mark_completed, mark_in_progress, etc.)"
        ),
        tags=["Therapy Sessions"]
    ),
    destroy=extend_schema(
        summary="Delete therapy session",
        description=(
            "Remove a therapy session from the system.\n\n"
            "⚠️ WARNING: This action cannot be undone and will affect:\n"
            "- Associated video recordings\n"
            "- Emotion analysis data\n"
            "- Session feedback\n\n"
            "Restrictions:\n"
            "- Cannot delete completed sessions with feedback\n"
            "- User must have access to the resident's care home"
        ),
        tags=["Therapy Sessions"]
    )
)

class SessionViewSet(viewsets.ModelViewSet):
    queryset = TherapySession.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'resident']
    search_fields = ['resident__name', 'notes']
    ordering_fields = ['scheduled_date', 'created_at', 'updated_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SessionCreateUpdateSerializer
        return SessionSerializer
    
    def get_queryset(self):
        queryset = TherapySession.objects.all()
        
        # Filter by status categories
        status_category = self.request.query_params.get('status_category', None)
        now = timezone.now()
        
        if status_category == 'completed':
            queryset = queryset.filter(status='completed')
        elif status_category == 'upcoming':
            queryset = queryset.filter(status='scheduled', scheduled_date__gt=now)
        elif status_category == 'past_due':
            queryset = queryset.filter(status='scheduled', scheduled_date__lt=now)
        elif status_category == 'in_progress':
            queryset = queryset.filter(status='in_progress')
        elif status_category == 'today':
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start.replace(hour=23, minute=59, second=59)
            queryset = queryset.filter(scheduled_date__range=(today_start, today_end))
        
        # Filter by feedback status
        feedback_status = self.request.query_params.get('feedback_status', None)
        if feedback_status == 'completed':
            queryset = queryset.exclude(feedback=None)
        elif feedback_status == 'pending':
            queryset = queryset.filter(status='completed', feedback=None)
        
        return queryset
    
    @extend_schema(
        summary="Mark session as completed",
        description=(
            "Mark a therapy session as completed and record end time.\n\n"
            "Automatic Actions:\n"
            "- Sets status to 'completed'\n"
            "- Records current timestamp as end_time\n"
            "- Enables feedback creation\n\n"
            "Requirements:\n"
            "- Session must be 'in_progress' or 'scheduled'\n"
            "- User must have access to the resident's care home"
        ),
        request=None,
        responses={
            200: OpenApiExample(
                'Success Response',
                value={'status': 'Session marked as completed'}
            )
        },
        tags=["Therapy Sessions"]
    )
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        session = self.get_object()
        session.status = 'completed'
        session.end_time = timezone.now()
        session.save()
        return Response(
            {'status': 'Session marked as completed'},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Mark session as in progress",
        description=(
            "Mark a therapy session as currently in progress.\n\n"
            "Use Cases:\n"
            "- Starting a scheduled session\n"
            "- Resuming a paused session\n"
            "- Indicating active therapy is occurring\n\n"
            "Requirements:\n"
            "- Session must be 'scheduled' status\n"
            "- User must have access to the resident's care home"
        ),
        request=None,
        responses={
            200: OpenApiExample(
                'Success Response',
                value={'status': 'Session marked as in progress'}
            )
        },
        tags=["Therapy Sessions"]
    )
    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        session = self.get_object()
        session.status = 'in_progress'
        session.save()
        return Response(
            {'status': 'Session marked as in progress'},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Cancel therapy session",
        description=(
            "Cancel a scheduled or in-progress therapy session.\n\n"
            "Use Cases:\n"
            "- Resident unavailable for scheduled session\n"
            "- Equipment issues preventing session\n"
            "- Emergency cancellation needs\n\n"
            "Business Rules:\n"
            "- Cannot cancel completed sessions\n"
            "- Cancellation reason should be noted in session notes\n"
            "- User must have access to the resident's care home"
        ),
        request=None,
        responses={
            200: OpenApiExample(
                'Success Response',
                value={'status': 'Session cancelled'}
            )
        },
        tags=["Therapy Sessions"]
    )
    @action(detail=True, methods=['post'])
    def cancel_session(self, request, pk=None):
        session = self.get_object()
        session.status = 'cancelled'
        session.save()
        return Response(
            {'status': 'Session cancelled'},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Get session videos with analysis endpoints",
        description=(
            "Retrieve all video recordings associated with this therapy "
            "session along with their emotion analysis endpoint URLs.\n\n"
            "Response Includes:\n"
            "- Complete video metadata\n"
            "- Direct URLs to emotion analysis endpoints\n"
            "- Frame-by-frame analysis access\n"
            "- Timeline and summary analysis links\n\n"
            "Analysis Endpoints Provided:\n"
            "- frames: Individual frame emotion analysis\n"
            "- timeline: Emotion progression over time\n"
            "- summary: Overall session emotion summary"
        ),
        responses={
            200: OpenApiExample(
                'Video Analysis Response',
                description='Session videos with analysis endpoints',
                value=[
                    {
                        'id': '123e4567-e89b-12d3-a456-426614174000',
                        'title': 'VR Session Recording',
                        'description': 'Main therapy session recording',
                        'file': ('http://127.0.0.1:8000/media/videos/'
                                'session_recording.mp4'),
                        'uploaded_at': '2024-09-03T14:30:00Z',
                        'status': 'completed',
                        'emotion_analysis_urls': {
                            'frames': ('http://127.0.0.1:8000/api/analysis/'
                                     'videos/123e4567-e89b-12d3-a456-426614174000/'
                                     'frames/'),
                            'timeline': ('http://127.0.0.1:8000/api/analysis/'
                                       'videos/123e4567-e89b-12d3-a456-426614174000/'
                                       'timeline/'),
                            'summary': ('http://127.0.0.1:8000/api/analysis/'
                                      'videos/123e4567-e89b-12d3-a456-426614174000/'
                                      'summary/')
                        }
                    }
                ]
            )
        },
        tags=["Therapy Sessions"]
    )
    @action(detail=True, methods=['get'], url_path='videos')
    def session_videos(self, request, pk=None):
        """
        Get all videos associated with this therapy session along with their analysis endpoints
        """
        session = self.get_object()
        videos = Video.objects.filter(therapy_session=session)
        data = []

        for video in videos:
            video_data = VideoSerializer(video).data
            # Add URLs for emotion analysis endpoints
            video_data['emotion_analysis_urls'] = {
                'frames': request.build_absolute_uri(
                    f'/api/analysis/videos/{video.id}/frames/'
                ),
                'timeline': request.build_absolute_uri(
                    f'/api/analysis/videos/{video.id}/timeline/'
                ),
                'summary': request.build_absolute_uri(
                    f'/api/analysis/videos/{video.id}/summary/'
                )
            }
            data.append(video_data)

        return Response(data)
