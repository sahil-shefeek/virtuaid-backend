from rest_framework import serializers
from residents.models import Resident
from therapy_sessions.models import TherapySession
from .models import Video, EmotionAnalysis, EmotionAnalysisSummary

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'file', 'file_size',
            'uploaded_at', 'updated_at', 'therapy_session', 'resident', 'status'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at', 'file_size', 'status']

class VideoInitSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    file_size = serializers.IntegerField(min_value=1)
    therapy_session = serializers.PrimaryKeyRelatedField(
        queryset=TherapySession.objects.all(),
        required=False
    )
    resident = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        required=False
    )
    
    def create(self, validated_data):
        return Video.objects.create(**validated_data)

class ChunkUploadSerializer(serializers.Serializer):
    chunk = serializers.FileField()
    chunk_number = serializers.IntegerField(min_value=0)
    chunks_total = serializers.IntegerField(min_value=1)

class EmotionAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionAnalysis
        fields = [
            'id', 'video', 'timestamp', 'angry', 'disgust', 'fear', 'happy',
            'neutral', 'sad', 'surprised', 'dominant_emotion', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'dominant_emotion']

class EmotionAnalysisSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionAnalysisSummary
        fields = [
            'id', 'video', 'angry_avg', 'disgust_avg', 'fear_avg', 'happy_avg',
            'neutral_avg', 'sad_avg', 'surprised_avg', 'dominant_emotion',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'dominant_emotion']
