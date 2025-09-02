from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from carehome_managers.models import CarehomeManagers

from .models import CareHomes
from .serializers import CareHomeSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List Care Homes",
        description="""
        Retrieve a list of care homes based on the authenticated user's
        role and permissions.

        **Permission Levels:**
        - **Super Admin**: Access to all care homes in the system
        - **Admin**: Access to care homes they directly manage
        - **Manager**: Access to care homes they are assigned to manage
        - **Other users**: No access (empty list)

        The list is automatically filtered based on the user's role and
        associated care homes.
        """,
        tags=["Care Homes"]
    ),
    create=extend_schema(
        summary="Create Care Home",
        description="""
        Create a new care home in the system.
        
        **Validation Rules:**
        - Care home name and address combination must be unique
        - A unique care home code will be automatically generated
        
        **Required Fields:**
        - name: Name of the care home
        - address: Physical address of the care home
        - admin: Admin user responsible for the care home
        """,
        tags=["Care Homes"]
    ),
    retrieve=extend_schema(
        summary="Get Care Home Details",
        description="Retrieve detailed information about a specific care home.",
        tags=["Care Homes"]
    ),
    update=extend_schema(
        summary="Update Care Home",
        description="""
        Update all fields of a care home.

        **Note:** The care home code is auto-generated and cannot be
        manually updated.
        """,
        tags=["Care Homes"]
    ),
    partial_update=extend_schema(
        summary="Partially Update Care Home",
        description="""
        Update specific fields of a care home.

        **Note:** The care home code is auto-generated and cannot be
        manually updated.
        """,
        tags=["Care Homes"]
    ),
    destroy=extend_schema(
        summary="Delete Care Home",
        description="""
        Delete a care home from the system.

        **Warning:** This action is irreversible and will also remove all
        associated data.
        """,
        tags=["Care Homes"]
    )
)
class CareHomeViewSet(viewsets.ModelViewSet):
    queryset = CareHomes.objects.all()
    serializer_class = CareHomeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superadmin:
            return CareHomes.objects.all()
        elif user.is_admin:
            return CareHomes.objects.filter(admin=user)
        elif user.is_manager:
            # Get care homes managed by the current user
            managed_carehomes_ids = CarehomeManagers.objects.filter(
                manager=user
            ).values_list('carehome_id', flat=True)
            return CareHomes.objects.filter(id__in=managed_carehomes_ids)
        else:
            return CareHomes.objects.none()

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        address = request.data.get('address')

        if CareHomes.objects.filter(name=name, address=address).exists():
            raise ValidationError(
                'A care home with the same name and address already exists.'
            )

        return super().create(request, *args, **kwargs)
