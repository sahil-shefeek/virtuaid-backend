from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.exceptions import ValidationError
from associates.models import Associates
from associates.serializers import AssociatesSerializer, AssociatesCreateSerializer
from carehomemanagers.models import CarehomeManagers
from carehomes.models import CareHomes


class AssociateViewSet(viewsets.ModelViewSet):
    queryset = Associates.objects.all()
    serializer_class = AssociatesSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if not user.is_superadmin:
            if user.is_admin:
                queryset = queryset.filter(care_home__admin=user)
            elif user.is_manager:
                queryset = queryset.filter(care_home__carehomemanagers__manager=user)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return AssociatesCreateSerializer
        return AssociatesSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_admin:
            care_home = CareHomes.objects.filter(admin=user).first()
        elif user.is_manager:
            care_home_manager = CarehomeManagers.objects.filter(manager=user).first()
            if care_home_manager:
                care_home = care_home_manager.carehome
            else:
                care_home = None
        else:
            care_home = None

        if not care_home:
            raise ValidationError("Failed to create resident. Creating user does not have a care home assigned.")

        serializer.save(created_by=user, care_home=care_home)
