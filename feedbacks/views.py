from rest_framework import viewsets
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes

from carehome_managers.models import CarehomeManagers
from feedbacks.models import Feedback
from feedbacks.serializers import FeedbackSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List therapy session feedbacks",
        description=(
            "Retrieve a list of VR therapy session feedbacks with "
            "role-based filtering:\n\n"
            "- **SuperAdmin**: Access to all feedbacks across all residents\n"
            "- **Admin**: Access to feedbacks for residents in their care "
            "homes\n"
            "- **Manager**: Access to feedbacks for residents in care homes "
            "they manage\n\n"
            "Supports filtering by resident, date range, and pagination."
        ),
        parameters=[
            OpenApiParameter(
                name='resident',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter feedbacks by resident UUID',
                examples=[
                    OpenApiExample(
                        'Resident Filter',
                        value='123e4567-e89b-12d3-a456-426614174000',
                        description='Show feedbacks for specific resident'
                    ),
                ],
            ),
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter feedbacks from this date onwards',
                examples=[
                    OpenApiExample(
                        'Start Date',
                        value='2024-09-01',
                        description='Show feedbacks from September 1st, 2024'
                    ),
                ],
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter feedbacks up to this date',
                examples=[
                    OpenApiExample(
                        'End Date',
                        value='2024-09-30',
                        description='Show feedbacks up to September 30th, 2024'
                    ),
                ],
            ),
        ],
        tags=["Feedbacks"],
        examples=[
            OpenApiExample(
                'Feedback List Response',
                description='Sample response showing therapy session feedbacks',
                value={
                    "count": 15,
                    "next": "http://127.0.0.1:8000/api/feedbacks/?page=2",
                    "previous": None,
                    "results": [
                        {
                            'id': '123e4567-e89b-12d3-a456-426614174000',
                            'resident': '456e7890-e89b-12d3-a456-426614174001',
                            'session_date': '2024-09-02',
                            'session_duration': 45,
                            'vr_experience': 'Virtual beach walk experience',
                            'engagement_level': 4,
                            'satisfaction': 5,
                            'physical_impact': 3,
                            'cognitive_impact': 4,
                            'emotional_response': 'Calm and relaxed response',
                            'feedback_notes': 'Excellent session',
                            'created_at': '2024-09-02T14:30:00Z'
                        }
                    ]
                },
                response_only=True
            ),
        ]
    ),
    create=extend_schema(
        summary="Create therapy session feedback",
        description=(
            "Record feedback for a VR therapy session.\n\n"
            "**Permission Requirements:**\n"
            "- User must have access to the resident's care home\n"
            "- All rating fields must be between 1-5\n\n"
            "**Required Fields:**\n"
            "- resident: Must be a valid resident UUID\n"
            "- session_date: Date of the therapy session\n"
            "- session_duration: Duration in minutes\n"
            "- All rating fields (engagement_level, satisfaction, etc.)\n"
            "- VR experience description and emotional response"
        ),
        tags=["Feedbacks"]
    ),
    retrieve=extend_schema(
        summary="Get feedback details",
        description=(
            "Retrieve detailed information about a specific therapy "
            "session feedback.\n\n"
            "Access is restricted based on user permissions to the "
            "resident's care home."
        ),
        tags=["Feedbacks"]
    ),
    update=extend_schema(
        summary="Update feedback",
        description=(
            "Update all fields of a therapy session feedback.\n\n"
            "**Restrictions:**\n"
            "- User must have access to the resident's care home\n"
            "- All rating fields must remain between 1-5\n"
            "- Session date cannot be in the future"
        ),
        tags=["Feedbacks"]
    ),
    partial_update=extend_schema(
        summary="Partially update feedback",
        description=(
            "Update specific fields of a therapy session feedback.\n\n"
            "**Restrictions:**\n"
            "- User must have access to the resident's care home\n"
            "- Rating fields must be between 1-5 if provided"
        ),
        tags=["Feedbacks"]
    ),
    destroy=extend_schema(
        summary="Delete feedback",
        description=(
            "Remove a therapy session feedback from the system.\n\n"
            "**Warning:** This action cannot be undone. Consider the "
            "impact on therapy session history and reporting.\n\n"
            "**Restrictions:**\n"
            "- User must have access to the resident's care home"
        ),
        tags=["Feedbacks"]
    )
)
class FeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing VR therapy session feedbacks.

    Provides CRUD operations for therapy session feedback with role-based
    access control. Feedbacks contain detailed information about resident
    responses to VR therapy sessions including engagement levels,
    satisfaction scores, and qualitative observations.

    **Features:**
    - Role-based data filtering
    - Date range filtering
    - Resident-specific filtering
    - Comprehensive therapy session tracking
    """
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_fields = ['resident']
    # ordering_fields = ['session_date']

    def get_queryset(self):
        user = self.request.user

        # Filter based on user group
        if user.groups.filter(name='SuperAdmin').exists():
            return Feedback.objects.all()
        elif user.groups.filter(name='Admin').exists():
            return Feedback.objects.filter(resident__care_home__admin=user)
        elif user.groups.filter(name='Manager').exists():
            managed_carehomes = CarehomeManagers.objects.filter(
                manager=user
            ).values_list('carehome', flat=True)
            return Feedback.objects.filter(
                resident__care_home__in=managed_carehomes
            )
        else:
            return Feedback.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        resident_id = request.query_params.get('resident', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        if resident_id:
            queryset = queryset.filter(resident__id=resident_id)

        if start_date and end_date:
            queryset = queryset.filter(
                session_date__range=[start_date, end_date]
            )
        elif start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        elif end_date:
            queryset = queryset.filter(session_date__lte=end_date)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
