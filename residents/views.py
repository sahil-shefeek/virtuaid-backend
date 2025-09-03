from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.exceptions import ValidationError

from residents.models import Resident
from residents.serializers import ResidentSerializer, ResidentCreateSerializer
from carehome_managers.models import CarehomeManagers
from carehomes.models import CareHomes
from drf_spectacular.utils import (
    extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    list=extend_schema(
        summary="List residents",
        description=(
            "Retrieve a list of residents with role-based filtering:\n\n"
            "- **SuperAdmin**: Access to all residents across all care homes\n"
            "- **Admin**: Access to residents in their assigned care home "
            "only\n"
            "- **Manager**: Access to residents in care homes they manage\n\n"
            "Supports search by resident name using the 'search' parameter."
        ),
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search residents by name (case-insensitive)',
                examples=[
                    OpenApiExample(
                        'Search Example',
                        value='Eleanor',
                        description=(
                            'Search for residents with "Eleanor" in name'
                        )
                    ),
                ],
            ),
        ],
        tags=["Residents"],
        examples=[
            OpenApiExample(
                'Resident List Response',
                description='Sample response showing residents list',
                value={
                    "count": 25,
                    "next": "http://127.0.0.1:8000/api/residents/?page=2",
                    "previous": None,
                    "results": [
                        {
                            'url': ('http://127.0.0.1:8000/api/residents/'
                                   '123e4567-e89b-12d3-a456-426614174000/'),
                            'id': '123e4567-e89b-12d3-a456-426614174000',
                            'name': 'Eleanor Watson',
                            'date_of_birth': '1938-06-15',
                            'care_home': {'name': 'Sunrise Manor Care Home'},
                            'created_by': ('http://127.0.0.1:8000/api/users/'
                                          '456e789-e89b-12d3-a456-426614174000/')
                        }
                    ]
                },
                response_only=True
            ),
        ]
    ),
    create=extend_schema(
        summary="Create new resident",
        description=(
            "Create a new resident in the care home system.\n\n"
            "**Permission Requirements:**\n"
            "- Admin: Can create residents in their assigned care home\n"
            "- Manager: Can create residents in care homes they manage\n"
            "- SuperAdmin: Can create residents (care home auto-assigned)\n\n"
            "**Business Rules:**\n"
            "- Care home is automatically assigned based on user role\n"
            "- User must have an assigned care home to create residents\n"
            "- Date of birth must be in the past"
        ),
        request=ResidentCreateSerializer,
        responses={201: ResidentSerializer},
        tags=["Residents"]
    ),
    retrieve=extend_schema(
        summary="Get resident details",
        description=(
            "Retrieve detailed information about a specific resident.\n\n"
            "Access is restricted based on user permissions:\n"
            "- User must have access to the resident's care home"
        ),
        tags=["Residents"]
    ),
    update=extend_schema(
        summary="Update resident",
        description=(
            "Update all fields of a resident.\n\n"
            "**Restrictions:**\n"
            "- Care home cannot be changed through this endpoint\n"
            "- User must have access to the resident's care home\n"
            "- Date of birth must be valid"
        ),
        tags=["Residents"]
    ),
    partial_update=extend_schema(
        summary="Partially update resident",
        description=(
            "Update specific fields of a resident.\n\n"
            "**Restrictions:**\n"
            "- Care home cannot be changed\n"
            "- User must have access to the resident's care home"
        ),
        tags=["Residents"]
    ),
    destroy=extend_schema(
        summary="Delete resident",
        description=(
            "Remove a resident from the system.\n\n"
            "**Warning:** This action cannot be undone. All associated "
            "therapy sessions, feedbacks, and reports will be affected.\n\n"
            "**Restrictions:**\n"
            "- User must have access to the resident's care home\n"
            "- Consider the impact on related data before deletion"
        ),
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
                queryset = queryset.filter(
                    care_home__carehomemanagers__manager=user
                )
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
            care_home_manager = CarehomeManagers.objects.filter(
                manager=user
            ).first()
            if care_home_manager:
                care_home = care_home_manager.carehome
            else:
                care_home = None
        else:
            care_home = None

        if not care_home:
            raise ValidationError(
                "Failed to create resident. Creating user does not have "
                "a care home assigned."
            )

        serializer.save(created_by=user, care_home=care_home)
