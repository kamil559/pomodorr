# Generated by Django 3.0.5 on 2020-04-26 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_auto_20200426_0915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='pomodoro_number',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
