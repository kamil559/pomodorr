# Generated by Django 3.0.5 on 2020-04-30 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20200429_1136'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='break_length',
            field=models.DurationField(blank=True, default=None, null=True),
        ),
    ]
