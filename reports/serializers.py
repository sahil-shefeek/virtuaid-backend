from rest_framework import serializers
from residents.models import Resident
from reports.models import Reports


class ReportsSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='reports-detail')
    resident = serializers.HyperlinkedRelatedField(
        queryset=Resident.objects.all(),
        view_name='residents-detail'
    )

    class Meta:
        model = Reports
        fields = [
            'id',
            'url',
            'report_month',
            'resident',
            'description',
            'pdf'
        ]
