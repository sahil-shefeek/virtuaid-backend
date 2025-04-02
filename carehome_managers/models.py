import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from carehomes.models import CareHomes


class CarehomeManagers(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    carehome = models.ForeignKey(CareHomes, on_delete=models.RESTRICT)

    def save(self, *args, **kwargs):
        if CarehomeManagers.objects.filter(carehome_id=self.carehome_id).count() >= 5:
            raise ValidationError(f"{self.carehome_id} already has 5 managers.")
        super().save(*args, **kwargs)
