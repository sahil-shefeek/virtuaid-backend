from rest_framework import serializers
from .models import Session
from residents.serializers import ResidentSerializer

class SessionSerializer(serializers.ModelSerializer):
    resident_details = ResidentSerializer(source='resident', read_only=True)
    feedback_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = '__all__'
        
    def get_feedback_status(self, obj):
        if obj.feedback:
            return "Completed"
        elif obj.status == 'completed':
            return "Pending"
        else:
            return "Not Applicable"

class SessionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'
