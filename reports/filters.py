import django_filters
from .models import Reports


class ReportsFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="report_month", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="report_month", lookup_expr='lte')
    resident = django_filters.UUIDFilter(field_name="resident__id")

    class Meta:
        model = Reports
        fields = ['start_date', 'end_date', 'resident']
