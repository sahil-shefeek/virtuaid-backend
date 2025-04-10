import uuid
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
