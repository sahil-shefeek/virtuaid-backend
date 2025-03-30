import uuid
from django.conf import settings
from django.db import models
from carehomes.models import CareHomes


class Associates(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=125)
    date_of_birth = models.DateField()
    care_home = models.ForeignKey(
        CareHomes,
        on_delete=models.RESTRICT,
        related_name='residents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
