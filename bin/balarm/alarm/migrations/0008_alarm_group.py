# Generated by Django 4.2.16 on 2024-10-22 17:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alarm', '0007_group_userbungry_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='alarm',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='alarm.group'),
        ),
    ]