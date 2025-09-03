from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models import TherapySession
from residents.serializers import ResidentSerializer


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Complete Therapy Session',
            summary='Detailed therapy session information',
            description=(
                'Complete therapy session with resident details, status, '
                'and feedback information'
            ),
            value={
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'title': 'VR Nature Walk Therapy Session',
                'description': (
                    'Guided virtual reality session through peaceful forest '
                    'environment to promote relaxation and engagement'
                ),
                'resident': '456e7890-e89b-12d3-a456-426614174001',
                'resident_details': {
                    'url': ('http://127.0.0.1:8000/api/residents/'
                           '456e7890-e89b-12d3-a456-426614174001/'),
                    'id': '456e7890-e89b-12d3-a456-426614174001',
                    'name': 'Eleanor Watson',
                    'date_of_birth': '1938-06-15',
                    'care_home': {'name': 'Sunrise Manor Care Home'}
                },
                'scheduled_date': '2024-09-03T14:30:00Z',
                'duration': 45,
                'status': 'completed',
                'notes': (
                    'Session went very well. Resident was engaged and calm '
                    'throughout. Showed positive emotional response to nature '
                    'sounds and visuals.'
                ),
                'created_at': '2024-09-01T10:00:00Z',
                'updated_at': '2024-09-03T15:15:00Z',
                'end_time': '2024-09-03T15:15:00Z',
                'feedback': '789e1234-e89b-12d3-a456-426614174002',
                'feedback_status': 'Completed'
            },
            request_only=False,
            response_only=True,
        ),
    ]
)
class SessionSerializer(serializers.ModelSerializer):
    """
    Comprehensive therapy session serializer with resident details.
    
    Provides complete information about therapy sessions including:
    - Session scheduling and status information
    - Resident details with care home context
    - Feedback completion status
    - Session notes and duration
    
    **Status Values:**
    - scheduled: Session is planned for future
    - in_progress: Session is currently active
    - completed: Session finished successfully
    - cancelled: Session was cancelled
    
    **Feedback Status:**
    - Completed: Feedback has been recorded
    - Pending: Session completed but no feedback yet
    - Not Applicable: Session not completed
    """
    resident_details = ResidentSerializer(source='resident', read_only=True)
    feedback_status = serializers.SerializerMethodField()
    
    class Meta:
        model = TherapySession
        fields = '__all__'
        
    def get_feedback_status(self, obj):
        if obj.feedback:
            return "Completed"
        elif obj.status == 'completed':
            return "Pending"
        else:
            return "Not Applicable"


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Create Therapy Session',
            summary='Data required to schedule a therapy session',
            description=(
                'Essential information for creating a new therapy session '
                'including resident, timing, and session details'
            ),
            value={
                'title': 'Morning VR Relaxation Session',
                'description': (
                    'Calming virtual environment session focusing on '
                    'stress reduction and emotional well-being'
                ),
                'resident': '456e7890-e89b-12d3-a456-426614174001',
                'scheduled_date': '2024-09-04T10:00:00Z',
                'duration': 30,
                'status': 'scheduled',
                'notes': 'First session of the week, focus on relaxation'
            },
            request_only=True,
            response_only=False,
        ),
        OpenApiExample(
            'Update Session Status',
            summary='Update session to in-progress',
            description=(
                'Example of updating session status when therapy begins'
            ),
            value={
                'status': 'in_progress',
                'notes': 'Session started, resident responding well'
            },
            request_only=True,
            response_only=False,
        ),
    ]
)
class SessionCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating therapy sessions.
    
    Used for scheduling new therapy sessions and updating existing ones.
    Supports partial updates for status changes and note additions.
    
    **Required Fields for Creation:**
    - title: Descriptive name for the session
    - resident: UUID reference to the resident
    - scheduled_date: When the session is planned
    - duration: Session length in minutes
    
    **Common Update Scenarios:**
    - Status changes (scheduled → in_progress → completed)
    - Adding session notes
    - Updating scheduled times
    - Modifying session duration
    """
    class Meta:
        model = TherapySession
        fields = '__all__'
