from rest_framework import serializers
from residents.models import Resident
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'file', 'file_size',
            'uploaded_at', 'updated_at', 'resident'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at', 'file_size']

class VideoInitSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    file_size = serializers.IntegerField(min_value=1)
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
