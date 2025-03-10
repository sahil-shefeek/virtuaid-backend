# Generated by Django 4.2.13 on 2024-07-20 09:36

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('associates', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session_date', models.DateField()),
                ('session_duration', models.PositiveIntegerField()),
                ('vr_experience', models.TextField()),
                ('engagement_level', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('satisfaction', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('physical_impact', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('cognitive_impact', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('emotional_response', models.TextField()),
                ('feedback_notes', models.TextField(blank=True)),
                ('associate', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='associates.associates')),
            ],
        ),
    ]
