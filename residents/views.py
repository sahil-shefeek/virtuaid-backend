from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.exceptions import ValidationError
from residents.models import Resident
from residents.serializers import ResidentSerializer, ResidentCreateSerializer
from carehome_managers.models import CarehomeManagers
from carehomes.models import CareHomes
from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    list=extend_schema(
        summary="List residents",
        description="Retrieve a list of residents. Results are filtered based on user permissions.",
        tags=["Residents"]
    ),
    create=extend_schema(
        summary="Create new resident",
        description="Create a new resident in the care home system.",
        tags=["Residents"]
    ),
    retrieve=extend_schema(
        summary="Get resident details",
        description="Retrieve detailed information about a specific resident.",
        tags=["Residents"]
    ),
    update=extend_schema(
        summary="Update resident",
        description="Update all fields of a resident.",
        tags=["Residents"]
    ),
    partial_update=extend_schema(
        summary="Partially update resident",
        description="Update specific fields of a resident.",
        tags=["Residents"]
    ),
    destroy=extend_schema(
        summary="Delete resident",
        description="Remove a resident from the system.",
        tags=["Residents"]
    )
)
class ResidentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing residents in care homes.
    
    Provides CRUD operations for residents with role-based access control:
    - SuperAdmin: Access to all residents
    - Admin: Access to residents in their care homes only
    - Manager: Access to residents in care homes they manage
    
    Supports search by resident name and filtering capabilities.
    """
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
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
            return ResidentCreateSerializer
        return ResidentSerializer

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
