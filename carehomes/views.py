from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from carehomemanagers.models import CarehomeManagers
from .models import CareHomes
from .serializers import CareHomeSerializer


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
            managed_carehomes_ids = CarehomeManagers.objects.filter(manager=user).values_list('carehome_id', flat=True)
            return CareHomes.objects.filter(id__in=managed_carehomes_ids)
        else:
            return CareHomes.objects.none()

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        address = request.data.get('address')

        if CareHomes.objects.filter(name=name, address=address).exists():
            raise ValidationError('A care home with the same name and address already exists.')

        return super().create(request, *args, **kwargs)
