import uuid
import csv
import io
from django.db import models
from residents.models import Resident
from therapy_sessions.models import TherapySession

def video_upload_path(instance, filename):
    """Generate a unique path for uploaded videos"""
    return f'uploads/videos/{instance.id}/{filename}'

class Video(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=video_upload_path)
    file_size = models.BigIntegerField(default=0, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    therapy_session = models.ForeignKey(
        TherapySession, 
        on_delete=models.CASCADE, 
        related_name='videos',
        null=True,
        blank=True
    )
    # Keeping resident field as null=True to support migration
    resident = models.ForeignKey(
        Resident, 
        on_delete=models.CASCADE, 
        related_name='videos',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.file:
            # Update file_size if file is available
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_emotion_data_csv(self):
        """Generate a CSV file with emotion analysis data"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow(['Timestamp', 'Angry', 'Sad', 'Happy', 'Dominant Emotion'])
        
        # Write individual frame analysis data
        for analysis in self.emotion_analyses.all().order_by('timestamp'):
            writer.writerow([
                f"{analysis.timestamp:.2f}",
                f"{analysis.angry:.4f}",
                f"{analysis.sad:.4f}",
                f"{analysis.happy:.4f}",
                analysis.dominant_emotion
            ])
            
        return output.getvalue()
    
    def get_emotion_timeline_csv(self):
        """Generate a CSV file with emotion timeline segments"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow(['Start Time', 'End Time', 'Duration', 'Dominant Emotion'])
        
        # Write timeline segments
        for segment in self.emotion_timeline.all().order_by('start_time'):
            writer.writerow([
                f"{segment.start_time:.2f}",
                f"{segment.end_time:.2f}",
                f"{segment.duration:.2f}",
                segment.dominant_emotion
            ])
            
        return output.getvalue()


class EmotionAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='emotion_analyses')
    timestamp = models.FloatField(help_text="Timestamp in seconds from the start of the video")
    angry = models.FloatField(default=0.0)
    disgust = models.FloatField(default=0.0)
    fear = models.FloatField(default=0.0)
    happy = models.FloatField(default=0.0)
    neutral = models.FloatField(default=0.0)
    sad = models.FloatField(default=0.0)
    surprised = models.FloatField(default=0.0)
    dominant_emotion = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['video', 'timestamp']
        
    def save(self, *args, **kwargs):
        # Calculate the dominant emotion
        emotions = {
            'angry': self.angry,
            'disgust': self.disgust,
            'fear': self.fear,
            'happy': self.happy,
            'neutral': self.neutral,
            'sad': self.sad,
            'surprised': self.surprised
        }
        self.dominant_emotion = max(emotions, key=emotions.get)
        super().save(*args, **kwargs)


class EmotionTimeline(models.Model):
    """Model to store emotion timeline segments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='emotion_timeline')
    start_time = models.FloatField(help_text="Start time in seconds from the start of the video")
    end_time = models.FloatField(help_text="End time in seconds from the start of the video")
    duration = models.FloatField(help_text="Duration of this emotion segment in seconds")
    dominant_emotion = models.CharField(max_length=20)
    confidence = models.FloatField(default=0.0, help_text="Confidence score for this emotion segment")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['video', 'start_time']
        
    def __str__(self):
        return f"{self.video.title}: {self.dominant_emotion} from {self.start_time:.1f}s to {self.end_time:.1f}s"


class EmotionAnalysisSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='emotion_summary')
    angry_avg = models.FloatField(default=0.0)
    disgust_avg = models.FloatField(default=0.0)
    fear_avg = models.FloatField(default=0.0)
    happy_avg = models.FloatField(default=0.0)
    neutral_avg = models.FloatField(default=0.0)
    sad_avg = models.FloatField(default=0.0)
    surprised_avg = models.FloatField(default=0.0)
    dominant_emotion = models.CharField(max_length=20, blank=True)
    emotion_counts = models.JSONField(default=dict, help_text="Count of frames for each emotion")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate the dominant emotion
        emotions = {
            'angry': self.angry_avg,
            'disgust': self.disgust_avg,
            'fear': self.fear_avg,
            'happy': self.happy_avg,
            'neutral': self.neutral_avg,
            'sad': self.sad_avg,
            'surprised': self.surprised_avg
        }
        self.dominant_emotion = max(emotions, key=emotions.get)
        super().save(*args, **kwargs)
