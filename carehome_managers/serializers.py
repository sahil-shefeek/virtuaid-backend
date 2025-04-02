from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from carehomes.models import CareHomes
from .models import CarehomeManagers


class CareHomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareHomes
        fields = ['id', 'name', 'code', 'address']


class InterfaceUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'name']


class CarehomeManagerSerializer(serializers.ModelSerializer):
    carehome = CareHomeSerializer()
    manager = InterfaceUserSerializer()

    class Meta:
        model = CarehomeManagers
        fields = ['id', 'manager', 'carehome']

    def validate(self, data):
        carehome = data['carehome']
        if CarehomeManagers.objects.filter(carehome_id=carehome.id).count() >= 5:
            raise ValidationError(f"{carehome.name} already has 5 managers.")
        return data


class CreateCarehomeManagerSerializer(serializers.ModelSerializer):
    carehome_id = serializers.PrimaryKeyRelatedField(queryset=CareHomes.objects.all(), source='carehome')
    manager_id = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), source='manager')

    class Meta:
        model = CarehomeManagers
        fields = ['carehome_id', 'manager_id']

    def validate(self, data):
        carehome = data['carehome']
        if CarehomeManagers.objects.filter(carehome=carehome).count() >= 5:
            raise ValidationError(f"{carehome.name} already has 5 managers.")
        return data

    def create(self, validated_data):
        return CarehomeManagers.objects.create(**validated_data)
