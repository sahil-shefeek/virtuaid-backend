from rest_framework import serializers
from residents.models import Resident
from feedbacks.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
