from django.db.models import Q

from pomodorr.frames import models


def get_all_date_frames(**kwargs):
    return models.DateFrame.objects.all(**kwargs)


def get_all_date_frames_for_user(user, **kwargs):
    return models.DateFrame.objects.filter(task__project__user=user, **kwargs)


def get_all_date_frames_for_project(project, **kwargs):
    return models.DateFrame.objects.filter(task__project=project, **kwargs)


def get_all_date_frames_for_task(task, **kwargs):
    return models.DateFrame.objects.filter(task=task, **kwargs)


def get_breaks_inside_date_frame(date_frame_object, end=None):
    end = end if end is not None else date_frame_object.end

    if end is None:
        return

    return models.DateFrame.objects.filter(task=date_frame_object.task, start__gt=date_frame_object.start, end__lt=end,
                                           frame_type=models.DateFrame.break_type)


def get_pauses_inside_date_frame(date_frame_object, end=None):
    end = end if end is not None else date_frame_object.end

    if end is None:
        return

    return models.DateFrame.objects.filter(start__gt=date_frame_object.start, end__lt=end,
                                           frame_type=models.DateFrame.pause_type)


def get_latest_date_frame_in_progress_for_task(task_id, **kwargs):
    return models.DateFrame.objects.filter(
        task__id=task_id, start__isnull=False, end__isnull=True, **kwargs).order_by('start').last()


def get_colliding_date_frame_for_task(task_id, start=None, end=None, excluded_task_id=None):
    if end:
        colliding_date_frame = get_colliding_date_frame_by_end_value(task_id=task_id, end=end)
    else:
        colliding_date_frame = get_colliding_date_frame_by_start_value(task_id=task_id, start=start)

    if colliding_date_frame is not None and excluded_task_id is not None and colliding_date_frame.id == excluded_task_id:
        return None
    return colliding_date_frame


def get_colliding_date_frame_by_start_value(task_id, start):
    return models.DateFrame.objects.filter(
        Q(task__id=task_id) & (
            (Q(start__lt=start) & Q(end__isnull=True)) |
            (Q(start__lt=start) & Q(end__gt=start))
        )
    ).order_by('created').last()


def get_colliding_date_frame_by_end_value(task_id, end):
    return models.DateFrame.objects.filter(
        Q(task__id=task_id) & (
            (Q(start__lt=end) & Q(end__isnull=True)) |
            (Q(start__lt=end) & Q(end__gt=end))
        )
    ).order_by('created').last()
