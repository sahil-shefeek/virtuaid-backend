from django.contrib.auth.models import Group
from rest_framework_simplejwt.exceptions import InvalidToken

from carehomemanagers.models import CarehomeManagers
from .models import InterfaceUser
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class InterfaceUserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='interfaceuser-detail')

    class Meta:
        model = InterfaceUser
        fields = ['url', 'id', 'name', 'email', 'is_superadmin', 'is_admin', 'is_manager']


class InterfaceUserCreateSerializer(serializers.HyperlinkedModelSerializer):
    password = serializers.CharField(write_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='interfaceuser-detail')

    class Meta:
        model = InterfaceUser
        fields = ['url', 'id', 'name', 'email', 'password']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        name = validated_data['name']
        email = validated_data['email']
        password = validated_data['password']
        created_by = self.context['request'].user
        if self.user_type == 'admin':
            user = InterfaceUser.objects.create_admin(email, name, password, created_by=created_by)
        elif self.user_type == 'manager':
            user = InterfaceUser.objects.create_manager(email, name, password, created_by=created_by)
        else:
            raise serializers.ValidationError("Invalid user type.")
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        # Check if the user is a manager
        manager_group = Group.objects.get(name='Manager')
        if manager_group in user.groups.all():
            # Check if the manager is associated with a care home
            if not CarehomeManagers.objects.filter(manager=user).exists():
                raise InvalidToken('You are not associated with any care home as a manager.')

        data.update({
            'name': user.name,
            'is_admin': user.is_admin,
            'is_superadmin': user.is_superadmin,
            'is_manager': user.is_manager,
        })

        return data

class CustomUserDetailsSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = InterfaceUser
        fields = ("email", "name", "username", "is_admin", "avatar")
        read_only_fields = ("email", "is_admin")

    def get_avatar(self, obj):
        """
        Returns only the absolute URL for the avatar image suitable for frontend use.
        """
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None