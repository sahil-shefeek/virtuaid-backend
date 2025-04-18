from django.contrib.auth import get_user_model
from rest_framework import serializers

from carehomes.models import CareHomes
from .models import Resident


class CareHomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareHomes
        fields = ['name']


class ResidentSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='residents-detail')
    care_home = CareHomeSerializer(read_only=True)
    created_by = serializers.HyperlinkedRelatedField(
        queryset=get_user_model().objects.all(),
        view_name='interfaceuser-detail'
    )

    class Meta:
        model = Resident
        fields = ['url', 'id', 'name', 'date_of_birth', 'care_home', 'created_by']


class ResidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resident
        fields = ['name', 'date_of_birth']
