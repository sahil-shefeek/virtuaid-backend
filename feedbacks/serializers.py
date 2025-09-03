from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from feedbacks.models import Feedback


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Feedback Example',
            summary='Complete feedback session data',
            description=(
                'Sample feedback data showing all fields with realistic '
                'therapy session information'
            ),
            value={
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'resident': '456e7890-e89b-12d3-a456-426614174001',
                'session_date': '2024-09-02',
                'session_duration': 45,
                'vr_experience': (
                    'Resident participated in a virtual beach walk '
                    'experience. They seemed calm and engaged throughout '
                    'the session, occasionally commenting on the beautiful '
                    'scenery.'
                ),
                'engagement_level': 4,
                'satisfaction': 5,
                'physical_impact': 3,
                'cognitive_impact': 4,
                'emotional_response': (
                    'The resident smiled frequently during the session and '
                    'expressed feeling relaxed and happy afterward. They '
                    'mentioned it reminded them of holidays by the sea.'
                ),
                'feedback_notes': (
                    'Excellent session. Resident was very responsive and '
                    'calm. Recommend continuing with nature-based experiences.'
                ),
                'created_at': '2024-09-02T14:30:00Z'
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            'Create Feedback Request',
            summary='Data required to create feedback',
            description=(
                'Essential feedback data for recording therapy session '
                'outcomes and resident responses'
            ),
            value={
                'resident': '456e7890-e89b-12d3-a456-426614174001',
                'session_date': '2024-09-02',
                'session_duration': 30,
                'vr_experience': (
                    'Virtual garden tour with interactive elements'
                ),
                'engagement_level': 4,
                'satisfaction': 4,
                'physical_impact': 3,
                'cognitive_impact': 4,
                'emotional_response': (
                    'Positive response, resident seemed engaged and calm'
                ),
                'feedback_notes': 'Good session, resident responded well'
            },
            request_only=True,
            response_only=False,
        ),
    ]
)
class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for therapy session feedback data.

    Captures comprehensive feedback about VR therapy sessions including:
    - Session details (date, duration, experience type)
    - Resident response metrics (engagement, satisfaction, impact scores)
    - Qualitative observations (emotional response, notes)

    **Rating Scales:**
    - engagement_level: 1-5 (1=Very Low, 5=Very High)
    - satisfaction: 1-5 (1=Very Dissatisfied, 5=Very Satisfied)
    - physical_impact: 1-5 (1=Negative, 3=Neutral, 5=Very Positive)
    - cognitive_impact: 1-5 (1=Negative, 3=Neutral, 5=Very Positive)
    """
    class Meta:
        model = Feedback
        fields = '__all__'
