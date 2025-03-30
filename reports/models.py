import uuid
from django.db import models
from residents.models import Associates


class Reports(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_month = models.DateField()
    associate = models.ForeignKey(Associates, on_delete=models.RESTRICT)
    description = models.TextField(blank=True)
    pdf = models.FileField(upload_to='uploads/reports/')
