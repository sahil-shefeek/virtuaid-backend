import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, viewsets
from rest_framework.response import Response

from carehome_managers.models import CarehomeManagers
from carehome_managers.serializers import (
    CarehomeManagerSerializer,
    CreateCarehomeManagerSerializer,
    InterfaceUserSerializer
)
from carehomes.models import CareHomes


@extend_schema_view(
    list=extend_schema(
        summary="List Care Home Managers",
        description="""
        Retrieve a list of care home managers with various filtering options.

        **Query Parameters:**
        - **carehome**: Filter managers by specific care home UUID
        - **type=unassigned**: Get unassigned managers for assignment

        **Permission Levels:**
        - **Admin**: Can view managers for care homes they manage
        - **Others**: No access (empty list)

        **Special Filters:**
        - When `carehome` parameter is provided, returns managers for that
          specific care home
        - When `type=unassigned` is provided, returns managers who are not
          yet assigned to any care home
        """,
        parameters=[
            OpenApiParameter(
                name='carehome',
                description='UUID of the care home to filter managers',
                required=False,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample(
                        'Care Home Filter',
                        summary='Filter by care home UUID',
                        description='Get managers assigned to a specific home',
                        value='550e8400-e29b-41d4-a716-446655440000'
                    )
                ]
            ),
            OpenApiParameter(
                name='type',
                description='Special filter type',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=['unassigned'],
                examples=[
                    OpenApiExample(
                        'Unassigned Managers',
                        summary='Get unassigned managers',
                        description='Returns managers not assigned to any home',
                        value='unassigned'
                    )
                ]
            )
        ],
        tags=["Care Home Managers"]
    ),
    create=extend_schema(
        summary="Assign Manager to Care Home",
        description="""
        Assign a manager to a care home.

        **Validation Rules:**
        - Each care home can have a maximum of 5 managers
        - Manager must exist and be in the 'Manager' group
        - Care home must exist

        **Required Fields:**
        - carehome_id: UUID of the care home
        - manager_id: ID of the manager user
        """,
        examples=[
            OpenApiExample(
                'Assign Manager',
                summary='Example assignment',
                description='Assign manager with ID 123 to care home',
                value={
                    'carehome_id': '550e8400-e29b-41d4-a716-446655440000',
                    'manager_id': 123
                }
            )
        ],
        tags=["Care Home Managers"]
    ),
    retrieve=extend_schema(
        summary="Get Care Home Manager Details",
        description="""
        Retrieve details of a specific care home manager assignment.
        """,
        tags=["Care Home Managers"]
    ),
    update=extend_schema(
        summary="Update Care Home Manager Assignment",
        description="""
        Update a care home manager assignment.

        **Note:** This is typically used to change which care home a
        manager is assigned to, subject to the same validation rules.
        """,
        tags=["Care Home Managers"]
    ),
    partial_update=extend_schema(
        summary="Partially Update Manager Assignment",
        description="Partially update care home manager assignment details.",
        tags=["Care Home Managers"]
    ),
    destroy=extend_schema(
        summary="Remove Manager Assignment",
        description="""
        Remove a manager's assignment from a care home.

        **Effect:** The manager will no longer have access to the care home
        but will remain in the system for potential reassignment.
        """,
        tags=["Care Home Managers"]
    )
)
class CarehomeManagerViewSet(viewsets.ModelViewSet):
    queryset = CarehomeManagers.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCarehomeManagerSerializer
        return CarehomeManagerSerializer

    def list(self, request, *args, **kwargs):
        carehome_id = request.query_params.get('carehome')
        manager_type = request.query_params.get('type')
        user = request.user

        if carehome_id:
            try:
                carehome_uuid = uuid.UUID(carehome_id)
                managers = CarehomeManagers.objects.filter(
                    carehome=carehome_uuid
                )
                serializer = self.get_serializer(managers, many=True)
                return Response(serializer.data)
            except ValueError:
                return Response({"detail": "Invalid carehome."}, status=status.HTTP_400_BAD_REQUEST)

        if manager_type == 'unassigned':
            manager_group = Group.objects.get(name='Manager')
            all_managers = get_user_model().objects.filter(groups=manager_group, created_by=self.request.user)
            assigned_managers = CarehomeManagers.objects.values_list('manager_id', flat=True)
            unassigned_managers = all_managers.exclude(id__in=assigned_managers)

            serializer = InterfaceUserSerializer(unassigned_managers, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.groups.filter(name='Admin').exists():
            carehomes = CareHomes.objects.filter(admin=user)
            carehome_managers = CarehomeManagers.objects.filter(carehome__in=carehomes)
        else:
            carehome_managers = CarehomeManagers.objects.none()

        serializer = self.get_serializer(carehome_managers, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
        # Invalidate cache after deleting a carehome manager
        clear_carehome_managers_cache(sender=CarehomeManagers, instance=instance)


@receiver(post_save, sender=CarehomeManagers)
@receiver(post_delete, sender=CarehomeManagers)
def clear_carehome_managers_cache(sender, instance, **kwargs):
    # Invalidate the cache for all users since carehome manager changes affect all admins
    user_model = get_user_model()
    admin_users = user_model.objects.filter(groups__name='Admin')
    for user in admin_users:
        cache_key = f'carehome_managers_{user.id}'
        cache.delete(cache_key)


@receiver(post_save, sender=CareHomes)
@receiver(post_delete, sender=CareHomes)
def clear_carehomes_cache(sender, instance, **kwargs):
    # Invalidate the cache for all users since carehome changes affect all admins
    user_model = get_user_model()
    admin_users = user_model.objects.filter(groups__name='Admin')
    for user in admin_users:
        cache_key = f'carehome_managers_{user.id}'
        cache.delete(cache_key)
