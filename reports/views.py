from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters

from reports.filters import ReportsFilter
from reports.models import Reports
from reports.serializers import ReportsSerializer
from drf_spectacular.utils import (
    extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    list=extend_schema(
        summary="List monthly therapy reports",
        description=(
            "Retrieve a list of monthly therapy reports with role-based "
            "filtering:\n\n"
            "- **SuperAdmin**: Access to all reports across all residents\n"
            "- **Admin**: Access to reports for residents in their care "
            "homes\n"
            "- **Manager**: Access to reports for residents in care homes "
            "they manage\n\n"
            "Supports filtering by resident, date range, and ordering by "
            "report month."
        ),
        parameters=[
            OpenApiParameter(
                name='resident',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter reports by resident UUID',
                examples=[
                    OpenApiExample(
                        'Resident Filter',
                        value='123e4567-e89b-12d3-a456-426614174000',
                        description='Show reports for specific resident'
                    ),
                ],
            ),
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description=(
                    'Filter reports from this month onwards (YYYY-MM-DD, '
                    'day will be ignored)'
                ),
                examples=[
                    OpenApiExample(
                        'Start Date',
                        value='2024-09-01',
                        description='Show reports from September 2024 onwards'
                    ),
                ],
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description=(
                    'Filter reports up to this month (YYYY-MM-DD, '
                    'day will be ignored)'
                ),
                examples=[
                    OpenApiExample(
                        'End Date',
                        value='2024-12-31',
                        description='Show reports up to December 2024'
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
                        'Order by Month',
                        value='-report_month',
                        description='Order by report month (newest first)'
                    ),
                    OpenApiExample(
                        'Order by Resident',
                        value='resident',
                        description='Order by resident name'
                    ),
                ],
            ),
        ],
        tags=["Reports"],
        examples=[
            OpenApiExample(
                'Reports List Response',
                description='Sample response showing monthly therapy reports',
                value={
                    "count": 8,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            'id': '123e4567-e89b-12d3-a456-426614174000',
                            'url': ('http://127.0.0.1:8000/api/reports/'
                                   '123e4567-e89b-12d3-a456-426614174000/'),
                            'report_month': '2024-09-01',
                            'resident': ('http://127.0.0.1:8000/api/residents/'
                                        '456e789-e89b-12d3-a456-426614174001/'),
                            'description': 'September therapy summary',
                            'pdf': ('http://127.0.0.1:8000/media/uploads/'
                                   'reports/september_2024_report.pdf')
                        }
                    ]
                },
                response_only=True
            ),
        ]
    ),
    create=extend_schema(
        summary="Create monthly therapy report",
        description=(
            "Generate a new monthly therapy report for a resident.\n\n"
            "**Permission Requirements:**\n"
            "- User must have access to the resident's care home\n"
            "- Report month must be valid and not in the future\n\n"
            "**Required Fields:**\n"
            "- resident: Must be a valid resident reference\n"
            "- report_month: First day of the month (YYYY-MM-01)\n"
            "- pdf: PDF file containing the detailed report\n\n"
            "**Business Rules:**\n"
            "- One report per resident per month\n"
            "- PDF file size limit: 10MB\n"
            "- Supported format: PDF only"
        ),
        tags=["Reports"]
    ),
    retrieve=extend_schema(
        summary="Get report details",
        description=(
            "Retrieve detailed information about a specific monthly "
            "therapy report.\n\n"
            "Includes direct download link to the PDF file. Access is "
            "restricted based on user permissions to the resident's "
            "care home."
        ),
        tags=["Reports"]
    ),
    update=extend_schema(
        summary="Update report",
        description=(
            "Update all fields of a monthly therapy report.\n\n"
            "**Restrictions:**\n"
            "- User must have access to the resident's care home\n"
            "- Report month cannot be changed after creation\n"
            "- PDF file must be valid if provided"
        ),
        tags=["Reports"]
    ),
    partial_update=extend_schema(
        summary="Partially update report",
        description=(
            "Update specific fields of a monthly therapy report.\n\n"
            "**Common Use Cases:**\n"
            "- Update description with additional insights\n"
            "- Replace PDF file with updated version\n\n"
            "**Restrictions:**\n"
            "- User must have access to the resident's care home"
        ),
        tags=["Reports"]
    ),
    destroy=extend_schema(
        summary="Delete report",
        description=(
            "Remove a monthly therapy report from the system.\n\n"
            "**Warning:** This action cannot be undone and will "
            "permanently delete the associated PDF file.\n\n"
            "**Restrictions:**\n"
            "- User must have access to the resident's care home\n"
            "- Consider backup requirements before deletion"
        ),
        tags=["Reports"]
    )
)
class ReportsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing monthly therapy reports.

    Provides CRUD operations for comprehensive monthly reports that
    summarize resident therapy progress, session outcomes, and
    recommendations. Reports are generated monthly and include
    detailed analysis of VR therapy effectiveness.

    **Features:**
    - Role-based data filtering
    - Date range filtering by report month
    - Resident-specific filtering
    - PDF file management and download
    - Ordered results by month or resident

    **Report Structure:**
    - Monthly summary of therapy sessions
    - Progress metrics and trends
    - Resident response analysis
    - Recommendations for future sessions
    """
    queryset = Reports.objects.all()
    serializer_class = ReportsSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = ReportsFilter
    ordering_fields = ['report_month', 'resident']
    ordering = ['report_month']

    def get_queryset(self):
        user = self.request.user
        if user.is_superadmin:
            return Reports.objects.all()
        elif user.is_admin:
            return Reports.objects.filter(resident__care_home__admin=user)
        elif user.is_manager:
            return Reports.objects.filter(
                resident__care_home__carehomemanagers__manager=user
            )
        return Reports.objects.none()
