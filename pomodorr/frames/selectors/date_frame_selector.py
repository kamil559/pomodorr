from datetime import datetime
from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import Q

from pomodorr.frames import models
from pomodorr.tools.utils import get_time_delta


def get_all_date_frames(**kwargs):
    return models.DateFrame.objects.all(**kwargs)


def get_all_date_frames_for_user(user: AbstractBaseUser, **kwargs):
    return models.DateFrame.objects.filter(task__project__user=user, **kwargs)


def get_finished_date_frames_for_user(user: AbstractBaseUser, **kwargs):
    return models.DateFrame.objects.filter(is_finished=True, task__project__user=user, **kwargs)


def get_finished_date_frames_for_task(task, **kwargs):
    return models.DateFrame.objects.filter(is_finished=True, task=task)


def get_all_date_frames_for_project(project, **kwargs):
    return models.DateFrame.objects.filter(task__project=project, **kwargs)


def get_all_date_frames_for_task(task, **kwargs):
    return models.DateFrame.objects.filter(task=task, **kwargs)


def get_breaks_inside_date_frame(date_frame_object, end=None):
    end = end if end is not None else date_frame_object.end

    if end is None:
        return models.DateFrame.objects.none()

    return models.DateFrame.objects.filter(task=date_frame_object.task, start__gt=date_frame_object.start, end__lt=end,
                                           frame_type=models.DateFrame.break_type)


def get_pauses_inside_date_frame(date_frame_object, end=None):
    end = end if end is not None else date_frame_object.end

    if end is None:
        return models.DateFrame.objects.none()

    return models.DateFrame.objects.filter(start__gt=date_frame_object.start, end__lt=end,
                                           frame_type=models.DateFrame.pause_type)


def get_latest_date_frame_in_progress_for_task(task_id: UUID, **kwargs):
    return models.DateFrame.objects.filter(
        task__id=task_id, start__isnull=False, end__isnull=True, **kwargs).order_by('start').last()


def get_colliding_date_frame_for_task(task_id: UUID, date: datetime, excluded_id: UUID = None):
    colliding_date_frame = models.DateFrame.objects.filter(
        Q(task__id=task_id) & (
            (Q(start__lt=date) & Q(end__isnull=True)) |
            (Q(start__lt=date) & Q(end__gt=date))
        )
    ).order_by('created').last()

    if colliding_date_frame and not colliding_date_frame.id == excluded_id:
        return colliding_date_frame


def get_obsolete_date_frames():
    #  Returns date frames that have been created at least one week ago
    return models.DateFrame.objects.filter(is_finished=False, start__date__lt=get_time_delta({'days': 7}, ahead=False))
