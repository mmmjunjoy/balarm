# Generated by Django 4.2.16 on 2024-09-05 08:23

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='alarm',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
