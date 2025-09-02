import uuid

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from rest_framework import serializers

from .models import CareHomes


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Care Home Example',
            summary='Complete care home data',
            description='Example of a care home with all required fields',
            value={
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'name': 'Sunshine Care Home',
                'code': 'SUN123',
                'address': '123 Main Street, Cityville, State 12345',
                'admin': 'http://example.com/api/users/1/'
            }
        )
    ]
)
class CareHomeSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for Care Home data.

    Handles the serialization and validation of care home information
    including automatic code generation upon creation.
    """

    class Meta:
        model = CareHomes
        fields = [
            'id',
            'url',
            'name',
            'code',
            'address',
            'admin'
        ]
        read_only_fields = ['code']  # Code is auto-generated

    def save(self, **kwargs):
        """
        Override save to auto-generate care home code.

        The code is generated using the first 3 characters of the name
        plus 3 random characters from a UUID.
        """
        name = self.validated_data.get('name')
        code = name[:3] + uuid.uuid4().hex[:3]
        self.validated_data['code'] = code
        return super().save(**kwargs)


