from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from residents.models import Resident
from therapy_sessions.models import TherapySession
from .models import Video, EmotionAnalysis, EmotionAnalysisSummary, EmotionTimeline

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Video Upload Response",
            summary="Example video after upload",
            description="Shows how video data appears after successful upload "
                       "with initial analysis status",
            value={
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Therapy Session - Patient Assessment",
                "description": "Video recording of patient interaction during "
                              "cognitive behavioral therapy session",
                "file": "/media/videos/therapy_session_001.mp4",
                "file_size": 52428800,
                "status": "pending",
                "uploaded_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "therapy_session": 1,
                "resident": 1
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            "Processing Video",
            summary="Video being analyzed",
            description="Video in processing state during emotion analysis",
            value={
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "Group Therapy Session",
                "description": "Multi-patient therapy session recording",
                "file": "/media/videos/group_therapy_002.mp4",
                "file_size": 104857600,
                "status": "processing",
                "uploaded_at": "2024-01-15T14:20:00Z",
                "updated_at": "2024-01-15T14:25:00Z",
                "therapy_session": 2,
                "resident": 3
            },
            request_only=False,
            response_only=True,
        )
    ]
)
class VideoSerializer(serializers.ModelSerializer):
    """
    Video serializer for handling therapy session video uploads and metadata.
    
    This serializer manages video files uploaded for emotion analysis and therapy
    documentation. Videos progress through states: pending -> processing -> 
    completed/failed.
    
    Features:
    - Automatic file size calculation
    - Status tracking for analysis pipeline
    - Integration with therapy sessions and residents
    - Read-only fields for system-managed data
    """
    class Meta:
        model = Video
        fields = '__all__'
        read_only_fields = ['id', 'file_size', 'status', 'uploaded_at', 'updated_at']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Basic Video Upload",
            summary="Simple video upload with title only",
            description="Minimal required data for video upload initialization",
            value={
                "title": "Morning Therapy Session",
                "description": "",
                "resident": None,
                "therapy_session": None
            },
            request_only=True,
            response_only=False,
        ),
        OpenApiExample(
            "Linked Video Upload",
            summary="Video upload linked to therapy session",
            description="Video upload with full therapy session context",
            value={
                "title": "CBT Session - Week 3",
                "description": "Cognitive behavioral therapy session focusing on "
                              "anxiety management techniques",
                "resident": 5,
                "therapy_session": 12
            },
            request_only=True,
            response_only=False,
        )
    ]
)
class VideoInitSerializer(serializers.Serializer):
    """
    Video initialization serializer for starting chunked uploads.
    
    This serializer handles the initial video upload request where metadata
    is provided before the actual video file chunks are uploaded. It establishes
    the video record and prepares for chunked file upload.
    
    Optional linking:
    - Can be linked to a specific therapy session
    - Can be associated with a specific resident
    - Both links are optional for flexibility
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    resident = serializers.PrimaryKeyRelatedField(queryset=Resident.objects.all(), required=False)
    therapy_session = serializers.PrimaryKeyRelatedField(queryset=TherapySession.objects.all(), required=False)
    
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "First Chunk Upload",
            summary="Uploading the first chunk of a video file",
            description="Example of uploading the first chunk in a multi-part "
                       "video file upload sequence",
            value={
                "chunk": "binary_data_here",
                "current_chunk_index": 0,
                "total_chunks": 5
            },
            request_only=True,
            response_only=False,
        ),
        OpenApiExample(
            "Final Chunk Upload",
            summary="Uploading the last chunk of a video file",
            description="Final chunk upload that completes the video file",
            value={
                "chunk": "binary_data_here",
                "current_chunk_index": 4,
                "total_chunks": 5
            },
            request_only=True,
            response_only=False,
        )
    ]
)
class ChunkUploadSerializer(serializers.Serializer):
    """
    Chunk upload serializer for handling large video file uploads.
    
    This serializer manages chunked file uploads to handle large video files
    efficiently. Files are split into chunks on the client side and uploaded
    sequentially. The server reassembles them once all chunks are received.
    
    Process flow:
    1. Client splits large video into chunks
    2. Each chunk is uploaded with its index and total count
    3. Server stores chunks temporarily
    4. Final chunk triggers file assembly and analysis
    """
    chunk = serializers.FileField()
    current_chunk_index = serializers.IntegerField()
    total_chunks = serializers.IntegerField()

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Happy Frame Analysis",
            summary="Frame showing predominantly happy emotion",
            description="Example emotion analysis for a frame where patient "
                       "shows happiness",
            value={
                "id": 1,
                "video": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 15.5,
                "angry": 0.02,
                "sad": 0.1,
                "happy": 0.88,
                "dominant_emotion": "happy",
                "created_at": "2024-01-15T10:35:00Z"
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            "Anxious Frame Analysis",
            summary="Frame showing elevated stress indicators",
            description="Analysis showing mixed emotions with concern indicators",
            value={
                "id": 2,
                "video": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 32.8,
                "angry": 0.15,
                "sad": 0.45,
                "happy": 0.4,
                "dominant_emotion": "sad",
                "created_at": "2024-01-15T10:35:15Z"
            },
            request_only=False,
            response_only=True,
        )
    ]
)
class EmotionAnalysisSerializer(serializers.ModelSerializer):
    """
    Individual emotion analysis frame serializer.
    
    This serializer represents the emotional analysis of a single frame
    within a video. Each frame is analyzed for multiple emotion types
    with confidence scores between 0.0 and 1.0.
    
    Emotion types tracked:
    - angry: Anger/frustration indicators
    - sad: Sadness/distress indicators  
    - happy: Joy/contentment indicators
    
    The dominant emotion is automatically determined based on the highest
    confidence score among all emotion types.
    """
    class Meta:
        model = EmotionAnalysis
        fields = [
            'id', 'video', 'timestamp', 'angry', 'sad', 'happy',
            'dominant_emotion', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'dominant_emotion']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Happy Period Timeline",
            summary="Timeline segment showing sustained happiness",
            description="Example timeline showing a period of consistent "
                       "positive emotional state",
            value={
                "id": 1,
                "video": "550e8400-e29b-41d4-a716-446655440000",
                "start_time": 120.0,
                "end_time": 185.5,
                "duration": 65.5,
                "dominant_emotion": "happy",
                "confidence": 0.85,
                "created_at": "2024-01-15T10:40:00Z"
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            "Transitional Period",
            summary="Timeline segment during emotional transition",
            description="Shorter timeline segment showing emotional change",
            value={
                "id": 2,
                "video": "550e8400-e29b-41d4-a716-446655440000",
                "start_time": 185.5,
                "end_time": 198.0,
                "duration": 12.5,
                "dominant_emotion": "sad",
                "confidence": 0.72,
                "created_at": "2024-01-15T10:40:15Z"
            },
            request_only=False,
            response_only=True,
        )
    ]
)
class EmotionTimelineSerializer(serializers.ModelSerializer):
    """
    Emotion timeline segment serializer.
    
    This serializer represents contiguous time periods within a video where
    a specific emotion remains dominant. Timeline segments help identify
    emotional patterns and transitions throughout therapy sessions.
    
    Timeline features:
    - Tracks emotional consistency periods
    - Provides confidence scores for dominant emotion
    - Calculates duration automatically
    - Helps identify emotional transitions and patterns
    
    Use cases:
    - Therapy progress monitoring
    - Emotional stability assessment
    - Treatment effectiveness evaluation
    """
    class Meta:
        model = EmotionTimeline
        fields = [
            'id', 'video', 'start_time', 'end_time', 'duration',
            'dominant_emotion', 'confidence', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Positive Session Summary",
            summary="Summary of a predominantly positive therapy session",
            description="Overall emotion analysis showing good therapeutic "
                       "response with detailed emotion counts",
            value={
                "id": 1,
                "video": "550e8400-e29b-41d4-a716-446655440000",
                "angry_avg": 0.12,
                "sad_avg": 0.25,
                "happy_avg": 0.63,
                "dominant_emotion": "happy",
                "emotion_counts": {
                    "happy": 1250,
                    "sad": 480,
                    "angry": 200,
                    "total_frames": 1930
                },
                "created_at": "2024-01-15T10:45:00Z",
                "updated_at": "2024-01-15T10:45:00Z"
            },
            request_only=False,
            response_only=True,
        ),
        OpenApiExample(
            "Challenging Session Summary",
            summary="Summary showing emotional difficulty",
            description="Analysis of a more challenging therapy session with "
                       "mixed emotional responses",
            value={
                "id": 2,
                "video": "550e8400-e29b-41d4-a716-446655440001",
                "angry_avg": 0.35,
                "sad_avg": 0.45,
                "happy_avg": 0.20,
                "dominant_emotion": "sad",
                "emotion_counts": {
                    "sad": 980,
                    "angry": 760,
                    "happy": 425,
                    "total_frames": 2165
                },
                "created_at": "2024-01-15T14:30:00Z",
                "updated_at": "2024-01-15T14:30:00Z"
            },
            request_only=False,
            response_only=True,
        )
    ]
)
class EmotionAnalysisSummarySerializer(serializers.ModelSerializer):
    """
    Comprehensive emotion analysis summary for entire video.
    
    This serializer provides aggregate emotion analysis across the complete
    video, offering insights into overall emotional patterns and therapeutic
    outcomes. It includes both statistical averages and frame counts.
    
    Summary metrics:
    - Average emotion scores across all analyzed frames
    - Total frame counts for each emotion type
    - Overall dominant emotion determination
    - Percentage distributions for detailed analysis
    
    Clinical applications:
    - Treatment effectiveness assessment
    - Progress tracking over multiple sessions
    - Comparative analysis between patients
    - Therapy optimization insights
    """
    emotion_counts = serializers.JSONField(required=False)
    
    class Meta:
        model = EmotionAnalysisSummary
        fields = [
            'id', 'video', 'angry_avg', 'sad_avg', 'happy_avg',
            'dominant_emotion', 'emotion_counts', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'dominant_emotion']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Complete Video Analysis",
            summary="Detailed video with completed emotion analysis",
            description="Full video details including comprehensive emotion "
                       "analysis summary and metadata",
            value={
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Weekly CBT Session - Progress Review",
                "description": "Cognitive behavioral therapy session focusing on "
                              "progress evaluation and goal setting",
                "file": "/media/videos/therapy_session_001.mp4",
                "file_size": 52428800,
                "uploaded_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:45:00Z",
                "status": "completed",
                "therapy_session": 1,
                "resident": 1,
                "emotion_summary": {
                    "id": 1,
                    "video": "550e8400-e29b-41d4-a716-446655440000",
                    "angry_avg": 0.12,
                    "sad_avg": 0.25,
                    "happy_avg": 0.63,
                    "dominant_emotion": "happy",
                    "emotion_counts": {
                        "happy": 1250,
                        "sad": 480,
                        "angry": 200,
                        "total_frames": 1930
                    },
                    "created_at": "2024-01-15T10:45:00Z",
                    "updated_at": "2024-01-15T10:45:00Z"
                }
            },
            request_only=False,
            response_only=True,
        )
    ]
)
class VideoDetailSerializer(serializers.ModelSerializer):
    """
    Detailed video serializer with comprehensive emotion analysis.
    
    This serializer provides complete video information including metadata,
    file details, and embedded emotion analysis summary. Used for detailed
    video views where comprehensive analysis data is needed.
    
    Includes:
    - Complete video metadata and file information
    - Processing status and timestamps
    - Embedded emotion analysis summary
    - Therapy session and resident relationships
    
    Ideal for:
    - Video detail pages in therapy management systems
    - Comprehensive progress reports
    - Clinical analysis dashboards
    - Research data export
    """
    emotion_summary = EmotionAnalysisSummarySerializer(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'file', 'file_size', 
            'uploaded_at', 'updated_at', 'status', 'therapy_session',
            'resident', 'emotion_summary'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_at', 'updated_at', 'status']
