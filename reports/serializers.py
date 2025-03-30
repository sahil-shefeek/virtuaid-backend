from rest_framework import serializers
from residents.models import Associates
from reports.models import Reports


class ReportsSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='reports-detail')
    associate = serializers.HyperlinkedRelatedField(
        queryset=Associates.objects.all(),
        view_name='residents-detail'
    )

    class Meta:
        model = Reports
        fields = [
            'id',
            'url',
            'report_month',
            'associate',
            'description',
            'pdf'
        ]
