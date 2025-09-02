from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from carehomes.models import CareHomes

from .models import CarehomeManagers


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Care Home',
            summary='Care home basic info',
            description='Basic care home information for manager assignment',
            value={
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'name': 'Sunshine Care Home',
                'code': 'SUN123',
                'address': '123 Main Street, Cityville, State 12345'
            }
        )
    ]
)
class CareHomeSerializer(serializers.ModelSerializer):
    """Basic care home information for manager assignments."""
    
    class Meta:
        model = CareHomes
        fields = ['id', 'name', 'code', 'address']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Manager User',
            summary='Manager user info',
            description='User information for managers',
            value={
                'id': 123,
                'email': 'manager@example.com',
                'name': 'John Manager'
            }
        )
    ]
)
class InterfaceUserSerializer(serializers.ModelSerializer):
    """User information serializer for managers."""
    
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'name']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Manager Assignment',
            summary='Complete manager assignment',
            description='Example of a manager assigned to a care home',
            value={
                'id': 1,
                'manager': {
                    'id': 123,
                    'email': 'manager@example.com',
                    'name': 'John Manager'
                },
                'carehome': {
                    'id': '550e8400-e29b-41d4-a716-446655440000',
                    'name': 'Sunshine Care Home',
                    'code': 'SUN123',
                    'address': '123 Main Street, Cityville, State 12345'
                }
            }
        )
    ]
)
class CarehomeManagerSerializer(serializers.ModelSerializer):
    """
    Serializer for care home manager assignments.
    
    Shows the relationship between managers and care homes
    with nested serialized data for both entities.
    """
    carehome = CareHomeSerializer()
    manager = InterfaceUserSerializer()

    class Meta:
        model = CarehomeManagers
        fields = ['id', 'manager', 'carehome']

    def validate(self, data):
        """
        Validate that care home doesn't exceed maximum manager limit.
        
        Each care home can have a maximum of 5 managers.
        """
        carehome = data['carehome']
        if CarehomeManagers.objects.filter(carehome_id=carehome.id).count() >= 5:
            raise ValidationError(f"{carehome.name} already has 5 managers.")
        return data


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Manager Assignment Creation',
            summary='Create manager assignment',
            description='Example for assigning a manager to a care home',
            value={
                'carehome_id': '550e8400-e29b-41d4-a716-446655440000',
                'manager_id': 123
            }
        )
    ]
)
class CreateCarehomeManagerSerializer(serializers.ModelSerializer):
    """
    Serializer for creating care home manager assignments.
    
    Uses simple ID references for both care home and manager
    to create the assignment relationship.
    """
    carehome_id = serializers.PrimaryKeyRelatedField(
        queryset=CareHomes.objects.all(),
        source='carehome',
        help_text="UUID of the care home"
    )
    manager_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        source='manager',
        help_text="ID of the manager user"
    )

    class Meta:
        model = CarehomeManagers
        fields = ['carehome_id', 'manager_id']

    def validate(self, data):
        """
        Validate that care home doesn't exceed maximum manager limit.
        
        Each care home can have a maximum of 5 managers.
        """
        carehome = data['carehome']
        if CarehomeManagers.objects.filter(carehome=carehome).count() >= 5:
            raise ValidationError(f"{carehome.name} already has 5 managers.")
        return data

    def create(self, validated_data):
        """Create a new care home manager assignment."""
        return CarehomeManagers.objects.create(**validated_data)
