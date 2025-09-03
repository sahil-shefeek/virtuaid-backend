from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from residents.models import Resident
from reports.models import Reports


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Monthly Report Example',
            summary='Complete monthly therapy report',
            description=(
                'Sample monthly report with resident information, '
                'description, and PDF file'
            ),
            value={
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'url': ('http://127.0.0.1:8000/api/reports/'
                       '123e4567-e89b-12d3-a456-426614174000/'),
                'report_month': '2024-09-01',
                'resident': ('http://127.0.0.1:8000/api/residents/'
                            '456e7890-e89b-12d3-a456-426614174001/'),
                'description': (
                    'September 2024 therapy report for Eleanor Watson. '
                    'This month showed significant improvement in engagement '
                    'levels during VR sessions. The resident participated '
                    'in 12 sessions with an average satisfaction score of '
                    '4.2/5. Notable progress in cognitive response and '
                    'emotional well-being. Recommend continuing with '
                    'nature-based VR experiences.'
                ),
                'pdf': ('http://127.0.0.1:8000/media/uploads/reports/'
                       'september_2024_watson_report.pdf')
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            'Create Report Request',
            summary='Data required to create a monthly report',
            description=(
                'Essential data for generating a monthly therapy report '
                'including resident reference and summary'
            ),
            value={
                'report_month': '2024-09-01',
                'resident': 'http://127.0.0.1:8000/api/residents/'
                           '456e7890-e89b-12d3-a456-426614174001/',
                'description': (
                    'September therapy summary showing good progress '
                    'in VR engagement and emotional response'
                ),
                'pdf': '<file_upload>'
            },
            request_only=True,
            response_only=False,
        ),
    ]
)
class ReportsSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for monthly therapy reports.

    Manages comprehensive monthly reports that summarize resident therapy
    progress, session outcomes, and recommendations. Each report covers
    a specific month and includes:

    **Key Features:**
    - Monthly therapy session summaries
    - Progress tracking and analysis
    - PDF report generation and storage
    - Resident-specific insights and recommendations

    **File Handling:**
    - PDF files are uploaded to /media/uploads/reports/
    - File size limits and format validation apply
    - Direct download links provided in responses
    """
    url = serializers.HyperlinkedIdentityField(view_name='reports-detail')
    resident = serializers.HyperlinkedRelatedField(
        queryset=Resident.objects.all(),
        view_name='residents-detail'
    )

    class Meta:
        model = Reports
        fields = [
            'id',
            'url',
            'report_month',
            'resident',
            'description',
            'pdf'
        ]
