# Generated by Django 3.0.5 on 2020-04-22 16:17

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_auto_20200421_0808'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='pomodoro_length',
            field=models.DurationField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='taskevent',
            name='duration',
            field=models.DurationField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='taskevent',
            name='start',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='start'),
        ),
        migrations.CreateModel(
            name='Gap',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('start', models.DateTimeField(default=django.utils.timezone.now, verbose_name='start')),
                ('end', models.DateTimeField(blank=True, default=None, null=True, verbose_name='end')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('task_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gaps', to='projects.TaskEvent')),
            ],
            options={
                'verbose_name_plural': 'Gaps',
                'ordering': ('created_at',),
            },
        ),
    ]
