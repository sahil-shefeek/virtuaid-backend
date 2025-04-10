from rest_framework import serializers
from residents.models import Resident
from therapy_sessions.models import TherapySession
from .models import Video, EmotionAnalysis, EmotionAnalysisSummary, EmotionTimeline

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'
        read_only_fields = ['id', 'file_size', 'status', 'uploaded_at', 'updated_at']

class VideoInitSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    resident = serializers.PrimaryKeyRelatedField(queryset=Resident.objects.all(), required=False)
    therapy_session = serializers.PrimaryKeyRelatedField(queryset=TherapySession.objects.all(), required=False)
    
class ChunkUploadSerializer(serializers.Serializer):
    chunk = serializers.FileField()
    current_chunk_index = serializers.IntegerField()
    total_chunks = serializers.IntegerField()

class EmotionAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionAnalysis
        fields = [
            'id', 'video', 'timestamp', 'angry', 'sad', 'happy',
            'dominant_emotion', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'dominant_emotion']

class EmotionTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionTimeline
        fields = [
            'id', 'video', 'start_time', 'end_time', 'duration',
            'dominant_emotion', 'confidence', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class EmotionAnalysisSummarySerializer(serializers.ModelSerializer):
    emotion_counts = serializers.JSONField(required=False)
    
    class Meta:
        model = EmotionAnalysisSummary
        fields = [
            'id', 'video', 'angry_avg', 'sad_avg', 'happy_avg',
            'dominant_emotion', 'emotion_counts', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'dominant_emotion']

class VideoDetailSerializer(serializers.ModelSerializer):
    """Detailed video serializer with emotion analysis summary and timeline"""
    emotion_summary = EmotionAnalysisSummarySerializer(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'file', 'file_size', 
            'uploaded_at', 'updated_at', 'status', 'therapy_session',
            'resident', 'emotion_summary'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_at', 'updated_at', 'status']
