from rest_framework import viewsets, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from carehome_managers.models import CarehomeManagers
from carehome_managers.serializers import CarehomeManagerSerializer, InterfaceUserSerializer, \
    CreateCarehomeManagerSerializer
from carehomes.models import CareHomes
import uuid
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


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
                managers = CarehomeManagers.objects.filter(carehome=carehome_uuid)
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

# from rest_framework import viewsets, status
# from rest_framework.response import Response
# from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Group
# from carehome_managers.models import CarehomeManagers
# from carehome_managers.serializers import CarehomeManagerSerializer, InterfaceUserSerializer
# from carehomes.models import CareHomes
# import uuid
# from django.core.cache import cache
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
#
#
# class CarehomeManagerViewSet(viewsets.ModelViewSet):
#     queryset = CarehomeManagers.objects.all()
#     serializer_class = CarehomeManagerSerializer
#
#     def list(self, request, *args, **kwargs):
#         carehome_id = request.query_params.get('carehome')
#         manager_type = request.query_params.get('type')
#         user = request.user
#
#         if carehome_id:
#             try:
#                 carehome_uuid = uuid.UUID(carehome_id)
#                 managers = CarehomeManagers.objects.filter(carehome=carehome_uuid)
#                 serializer = self.get_serializer(managers, many=True)
#                 return Response(serializer.data)
#             except ValueError:
#                 return Response({"detail": "Invalid carehome."}, status=status.HTTP_400_BAD_REQUEST)
#
#         if manager_type == 'unassigned':
#             manager_group = Group.objects.get(name='Manager')
#             all_managers = get_user_model().objects.filter(groups=manager_group)
#             assigned_managers = CarehomeManagers.objects.values_list('manager_id', flat=True)
#             unassigned_managers = all_managers.exclude(id__in=assigned_managers)
#
#             serializer = InterfaceUserSerializer(unassigned_managers, many=True, context={'request': request})
#             return Response(serializer.data, status=status.HTTP_200_OK)
#
#         if user.groups.filter(name='Admin').exists():
#             carehomes = CareHomes.objects.filter(admin=user)
#             carehome_managers = CarehomeManagers.objects.filter(carehome__in=carehomes)
#         else:
#             carehome_managers = CarehomeManagers.objects.none()
#
#         serializer = self.get_serializer(carehome_managers, many=True)
#         return Response(serializer.data)
#
#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         self.perform_destroy(instance)
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#     def perform_destroy(self, instance):
#         instance.delete()
#         # Invalidate cache after deleting a carehome manager
#         clear_carehome_managers_cache(sender=CarehomeManagers, instance=instance)
#
#
# @receiver(post_save, sender=CarehomeManagers)
# @receiver(post_delete, sender=CarehomeManagers)
# def clear_carehome_managers_cache(sender, instance, **kwargs):
#     # Invalidate the cache for all users since carehome manager changes affect all admins
#     user_model = get_user_model()
#     admin_users = user_model.objects.filter(groups__name='Admin')
#     for user in admin_users:
#         cache_key = f'carehome_managers_{user.id}'
#         cache.delete(cache_key)
#
#
# @receiver(post_save, sender=CareHomes)
# @receiver(post_delete, sender=CareHomes)
# def clear_carehomes_cache(sender, instance, **kwargs):
#     # Invalidate the cache for all users since carehome changes affect all admins
#     user_model = get_user_model()
#     admin_users = user_model.objects.filter(groups__name='Admin')
#     for user in admin_users:
#         cache_key = f'carehome_managers_{user.id}'
#         cache.delete(cache_key)
