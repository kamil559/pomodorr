# Generated by Django 3.0.5 on 2020-04-29 12:37

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0002_auto_20200429_1136'),
    ]

    operations = [
        migrations.CreateModel(
            name='DateFrame',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('start', models.DateTimeField(default=django.utils.timezone.now, verbose_name='start')),
                ('end', models.DateTimeField(blank=True, default=None, null=True, verbose_name='end')),
                ('duration', models.DurationField(blank=True, default=None, null=True)),
                ('type', model_utils.fields.StatusField(choices=[(0, 'pomodor'), (1, 'break'), (2, 'pause')], default=0, max_length=100, no_check_for_status=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='frames', to='projects.Task')),
            ],
            options={
                'verbose_name_plural': 'DateFrames',
                'ordering': ('created',),
            },
        ),
        migrations.AddIndex(
            model_name='dateframe',
            index=models.Index(condition=models.Q(('start__isnull', False), ('end__isnull', False)), fields=['start', 'end'], name='start_end_idx'),
        ),
    ]
