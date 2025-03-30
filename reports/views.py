from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from reports.filters import ReportsFilter
from reports.models import Reports
from reports.serializers import ReportsSerializer


class ReportsViewSet(viewsets.ModelViewSet):
    queryset = Reports.objects.all()
    serializer_class = ReportsSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = ReportsFilter
    ordering_fields = ['report_month', 'resident']
    ordering = ['report_month']

    def get_queryset(self):
        user = self.request.user
        if user.is_superadmin:
            return Reports.objects.all()
        elif user.is_admin:
            return Reports.objects.filter(resident__care_home__admin=user)
        elif user.is_manager:
            return Reports.objects.filter(resident__care_home__carehomemanagers__manager=user)
        return Reports.objects.none()
