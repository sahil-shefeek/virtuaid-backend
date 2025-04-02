from django.db import models
from residents.models import Resident
from feedbacks.models import Feedback

class Session(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='sessions')
    scheduled_date = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, null=True)
    feedback = models.OneToOneField(Feedback, on_delete=models.SET_NULL, null=True, blank=True, related_name='session')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Session for {self.resident} on {self.scheduled_date}"
