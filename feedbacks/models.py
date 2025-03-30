import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from residents.models import Resident


class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resident = models.ForeignKey(Resident, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    session_date = models.DateField()
    session_duration = models.PositiveIntegerField()
    vr_experience = models.TextField()
    engagement_level = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    satisfaction = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    physical_impact = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    cognitive_impact = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    emotional_response = models.TextField()
    feedback_notes = models.TextField(
        blank=True
    )
