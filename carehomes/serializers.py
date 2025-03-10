import uuid

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import CareHomes


class CareHomeSerializer(serializers.HyperlinkedModelSerializer):
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

    def save(self, **kwargs):
        name = self.validated_data.get('name')
        code = name[:3] + uuid.uuid4().hex[:3]
        self.validated_data['code'] = code
        return super().save(**kwargs)


