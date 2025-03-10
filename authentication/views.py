from django.contrib.auth.models import Group
from rest_framework import viewsets, status, generics
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView
from authentication.models import InterfaceUser
from authentication.serializers import InterfaceUserSerializer, InterfaceUserCreateSerializer, \
    CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework_simplejwt.serializers import TokenVerifySerializer, TokenBlacklistSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import exceptions, status
from rest_framework.response import Response
from django.conf import settings


class UserDetailView(generics.RetrieveAPIView):
    queryset = InterfaceUser.objects.all()
    serializer_class = InterfaceUserSerializer

    def get_object(self):
        return self.request.user


class InterfaceUserViewSet(viewsets.ModelViewSet):
    queryset = InterfaceUser.objects.all()
    serializer_class = InterfaceUserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return InterfaceUserCreateSerializer
        return InterfaceUserSerializer

    def create(self, request, *args, **kwargs):
        user_type = request.query_params.get('type')
        serializer = self.get_serializer(data=request.data, user_type=user_type)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = InterfaceUser.objects.all()
        user_type = self.request.query_params.get('type')

        if not self.request.user.is_superadmin:
            queryset = queryset.filter(created_by=self.request.user)

        if user_type == 'admin':
            admin_group = Group.objects.get(name='Admin')
            queryset = queryset.filter(groups=admin_group)
        elif user_type == 'manager':
            manager_group = Group.objects.get(name='Manager')
            queryset = queryset.filter(groups=manager_group)

        return queryset


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.pop('refresh', None)
        max_age = 3600 * 24

        if refresh:
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE_NAME'],
                refresh,
                max_age=max_age,
                httponly=True,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = request.data.get('refresh')
        if not refresh:
            refresh = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_NAME'])

        if not refresh:
            raise exceptions.AuthenticationFailed('No refresh token provided')

        serializer = self.get_serializer(data={'refresh': refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        if not token:
            token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_NAME'])

        if not token:
            raise exceptions.AuthenticationFailed('Bad Request')

        serializer = TokenVerifySerializer(data={'token': token})
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenBlacklistView(TokenBlacklistView):
    def post(self, request, *args, **kwargs):
        # Try to get refresh token from request body
        refresh_token = request.data.get('refresh')

        # If not in body, try to get it from the cookie
        if not refresh_token:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_NAME'])

        # If still not found, raise an error
        if not refresh_token:
            raise exceptions.AuthenticationFailed('No refresh token provided')

        # Create a serializer with the refresh token
        serializer = TokenBlacklistSerializer(data={'refresh': refresh_token})

        try:
            # Validate and blacklist the token
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        response = Response(status=status.HTTP_205_RESET_CONTENT)

        # Clear the refresh token cookie
        response.delete_cookie(
            settings.SIMPLE_JWT['AUTH_COOKIE_NAME'],
            path='/',
            domain=settings.SIMPLE_JWT.get('AUTH_COOKIE_DOMAIN', None)
        )

        return response
