from django.contrib.auth import get_user_model
from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from carehomes.models import CareHomes
from .models import Resident


class CareHomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareHomes
        fields = ['name']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Resident Example',
            summary='Sample resident data',
            description=(
                'Complete resident information with care home and creator '
                'details'
            ),
            value={
                'url': ('http://127.0.0.1:8000/api/residents/'
                       '123e4567-e89b-12d3-a456-426614174000/'),
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'name': 'Eleanor Watson',
                'date_of_birth': '1938-06-15',
                'care_home': {
                    'name': 'Sunrise Manor Care Home'
                },
                'created_by': ('http://127.0.0.1:8000/api/users/'
                              '456e7890-e89b-12d3-a456-426614174000/')
            },
            request_only=False,
            response_only=True,
        ),
    ]
)
class ResidentSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for resident data with complete information including care home.

    Used for retrieving and updating existing residents. The care_home is
    read-only and automatically assigned based on the user's permissions
    during creation.
    """
    url = serializers.HyperlinkedIdentityField(view_name='residents-detail')
    care_home = CareHomeSerializer(read_only=True)
    created_by = serializers.HyperlinkedRelatedField(
        queryset=get_user_model().objects.all(),
        view_name='interfaceuser-detail'
    )

    class Meta:
        model = Resident
        fields = [
            'url', 'id', 'name', 'date_of_birth', 'care_home', 'created_by'
        ]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Create Resident Request',
            summary='Data required to create a new resident',
            description=(
                'Minimal data required for creating a resident. '
                'Care home assignment is automatic.'
            ),
            value={
                'name': 'Margaret Thompson',
                'date_of_birth': '1942-03-22'
            },
            request_only=True,
            response_only=False,
        ),
    ]
)
class ResidentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new residents.

    Only requires basic information. The care_home is automatically assigned:
    - Admin users: Their assigned care home
    - Manager users: Care home they manage
    - SuperAdmin: Must be specified in the request
    """
    class Meta:
        model = Resident
        fields = ['name', 'date_of_birth']
