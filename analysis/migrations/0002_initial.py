# Generated by Django 4.2.20 on 2025-04-07 07:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('analysis', '0001_initial'),
        ('residents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='resident',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='residents.resident'),
        ),
    ]
