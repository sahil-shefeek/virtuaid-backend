from rest_framework import serializers
from .models import TherapySession
from residents.serializers import ResidentSerializer

class SessionSerializer(serializers.ModelSerializer):
    resident_details = ResidentSerializer(source='resident', read_only=True)
    feedback_status = serializers.SerializerMethodField()
    
    class Meta:
        model = TherapySession
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
        model = TherapySession
        fields = '__all__'
