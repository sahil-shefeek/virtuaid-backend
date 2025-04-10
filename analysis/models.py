import uuid
from django.db import models
from residents.models import Resident
from therapy_sessions.models import TherapySession

def video_upload_path(instance, filename):
    """Generate a unique path for uploaded videos"""
    return f'uploads/videos/{instance.id}/{filename}'

class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=video_upload_path)
    file_size = models.BigIntegerField(default=0, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
