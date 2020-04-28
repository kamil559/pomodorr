import math
import operator
from copy import deepcopy
from datetime import timedelta
from functools import reduce

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from pomodorr.projects.exceptions import TaskException, TaskEventException
from pomodorr.projects.models import Project, Task, SubTask, TaskEvent
from pomodorr.projects.selectors import ProjectSelector, TaskSelector, TaskEventSelector, SubTaskSelector, GapSelector


class ProjectServiceModel:
    model = Project
    selector_class = ProjectSelector

    @classmethod
    def is_project_name_available(cls, user, name, exclude=None):
        query = cls.selector_class.get_active_projects_for_user(user=user, name=name)
        if exclude is not None:
            return not query.exclude(id=exclude.id).exists()
        return not query.exists()


class TaskServiceModel:
    model = Task
    task_selector = TaskSelector
    task_event_selector = TaskEventSelector

    def is_task_name_available(self, project, name, exclude=None):
        query = self.task_selector.get_active_tasks_for_user(user=project.user, project=project, name=name)
        if exclude is not None:
            return not query.exclude(id=exclude.id).exists()
        return not query.exists()

    def pin_to_project(self, task, project, db_save=True):
        if self.is_task_name_available(project=project, name=task.name):
            pinned_task = self.perform_pin(task=task, project=project, db_save=db_save)
            return pinned_task
        else:
            raise TaskException({'name': [TaskException.messages[TaskException.task_duplicated]]},
                                code=TaskException.task_duplicated)

    @staticmethod
    def perform_pin(task, project, db_save=True):
        pinned_task = task
        pinned_task.project = project

        if db_save:
            pinned_task.save()

        return pinned_task

    def complete_task(self, task, db_save=True):
        self.check_task_already_completed(task=task)
        active_task_event = self.task_event_selector.get_current_task_event_for_task(task=task)

        if active_task_event is not None:
            self.save_state_of_active_pomodoro(task_event=active_task_event)

        if task.repeat_duration is not None:
            archived_task = self.archive_task(task=task)
            self.create_next_task(task=archived_task)
            return archived_task
        else:
            task.status = self.model.status_completed
            if db_save:
                task.save()
            return task

    def create_next_task(self, task):
        next_task = deepcopy(task)
        next_task.id = None
        next_due_date = self.get_next_due_date(due_date=task.due_date, duration=task.repeat_duration)
        next_task.due_date = next_due_date
        next_task.status = self.model.status_active
        next_task.save()
        return next_task

    @staticmethod
    def archive_task(task):
        archived_task = task
        archived_task.status = Task.status_completed
        archived_task.save()
        return archived_task

    def reactivate_task(self, task, db_save=True):
        self.check_task_already_active(task=task)
        if not self.is_task_name_available(project=task.project, name=task.name):
            raise TaskException([TaskException.messages[TaskException.task_duplicated]],
                                code=TaskException.task_duplicated)

        task.status = self.model.status_active
        if db_save:
            task.save()
        return task

    @staticmethod
    def get_next_due_date(due_date, duration):
        if due_date is None:
            return timezone.now()
        return due_date + duration

    def check_task_already_completed(self, task):
        if task.status == self.model.status_completed:
            raise TaskException([TaskException.messages[TaskException.already_completed]],
                                code=TaskException.already_completed)

    def check_task_already_active(self, task):
        if task.status == self.model.status_active:
            raise TaskException([TaskException.messages[TaskException.already_active]],
                                code=TaskException.already_active)

    @staticmethod
    def save_state_of_active_pomodoro(task_event):
        if task_event.end is not None:
            raise TaskEventException([TaskEventException.messages[TaskEventException.already_completed]],
                                     code=TaskEventException.already_completed)
        else:
            task_event.end = timezone.now()
            task_event.save()


class SubTaskServiceModel:
    model = SubTask
    task_selector = SubTaskSelector

    def is_sub_task_name_available(self, task, name, exclude=None):
        query = self.task_selector.get_all_sub_tasks_for_task(task=task, name=name)
        if exclude is not None:
            return not query.exclude(id=exclude.id).exists()
        return not query.exists()


class TaskEventServiceModel:
    model = TaskEvent
    task_service_model = TaskServiceModel()
    task_event_selector = TaskEventSelector
    gap_selector = GapSelector

    def start_pomodoro(self, task):
        self.task_service_model.check_task_already_completed(task=task)
        pomodoro_start = timezone.now()

        self.check_current_task_event_already_exists(task=task, remove_outdated=True)
        self.check_datetime_available(task=task, start_date=pomodoro_start)

        new_pomodoro = self.perform_pomodoro_create(task=task, start=pomodoro_start)
        return new_pomodoro

    def finish_pomodoro(self, task_event, remove_unfinished_gaps=False):
        self.task_service_model.check_task_already_completed(task=task_event.task)
        finish_datetime = timezone.now()
        duration = self.get_task_event_duration(task_event=task_event, finish_datetime=finish_datetime)

        self.check_datetime_available(task=task_event.task, start_date=task_event.start, end_date=finish_datetime,
                                      excluded_task_event=task_event)

        task_event.end, task_event.duration = finish_datetime, duration
        task_event.save()

        if remove_unfinished_gaps:
            self.remove_gaps(task_event=task_event)

        return task_event

    def check_datetime_available(self, task, start_date, end_date=None, excluded_task_event=None):
        today = timezone.now().date()

        active_task_events_constraint = Q(start__isnull=False) & Q(end__isnull=True)
        completed_task_events_constraint = Q(start__isnull=False) & Q(end__isnull=False)
        today_date_constraint = Q(start__date=today) & Q(end__date=today)

        start_constraint, end_constraint = (Q(start__gte=start_date), Q(end__gte=start_date))

        overlapping_task_events = self.task_event_selector.get_all_task_events_for_task(
            task=task).filter(
            (active_task_events_constraint | completed_task_events_constraint) &
            today_date_constraint & (
                start_constraint | end_constraint
            )
        )

        if end_date is not None:
            start_constraint, end_constraint = (Q(start__gte=end_date), Q(end__gte=end_date))
            overlapping_task_events = overlapping_task_events.filter(
                start_constraint | end_constraint
            )

        if excluded_task_event is not None:
            overlapping_task_events = overlapping_task_events.exclude(id=excluded_task_event.id)

        if overlapping_task_events.exists():
            raise TaskEventException([TaskEventException.messages[TaskEventException.overlapping_pomodoro]],
                                     code=TaskEventException.overlapping_pomodoro)

    def perform_pomodoro_create(self, task, start):
        pomodoro = self.model(task=task, start=start)
        pomodoro.full_clean()
        pomodoro.save()

        return pomodoro

    def get_task_event_duration(self, task_event, finish_datetime):
        gaps_duration = reduce(operator.add, (gap.end - gap.start for gap in task_event.gaps.all()), timedelta(0))
        duration_without_gaps = finish_datetime - task_event.start - gaps_duration

        normalized_pomodoro_duration = self.normalize_pomodoro_duration(task_event=task_event,
                                                                        task_event_duration=duration_without_gaps,
                                                                        error_margin={'minutes': 1})

        return normalized_pomodoro_duration

    def normalize_pomodoro_duration(self, task_event_duration, task_event, error_margin):
        error_margin = timedelta(**error_margin)
        pomodoro_length = self.get_pomodoro_length(task=task_event.task)
        duration_difference = task_event_duration - pomodoro_length

        if duration_difference > error_margin:
            raise TaskEventException([TaskEventException.messages[TaskEventException.invalid_pomodoro_length]],
                                     code=TaskEventException.invalid_pomodoro_length)

        if timedelta(milliseconds=1) < duration_difference < error_margin:
            truncated_minutes = math.trunc(pomodoro_length.seconds / 60)
            return timedelta(minutes=truncated_minutes)

        return task_event_duration

    @staticmethod
    def get_pomodoro_length(task):
        # user = task_event.task.project.user
        # todo: create settings module where each user will have default values for pomodoros, breaks, long breaks, etc.
        # user_global_pomodoro_length = user.pomodoro_length
        task_specific_pomodoro_length = task.pomodoro_length

        if task_specific_pomodoro_length and task_specific_pomodoro_length is not None:
            return task_specific_pomodoro_length
        # return user_global_pomodoro_length

    def check_current_task_event_already_exists(self, task, remove_outdated=False):
        current_task_event = self.task_event_selector.get_current_task_event_for_task(task=task)

        if current_task_event is not None:
            self.check_current_task_event_is_connected(task_event=current_task_event)

        if remove_outdated:
            self.remove_task_event(task_event=current_task_event)

    @staticmethod
    def check_current_task_event_is_connected(task_event):
        connection_id = cache.get(task_event.id)

        if connection_id and connection_id is not None:
            raise TaskEventException([TaskEventException.messages[TaskEventException.current_pomodoro_exists]],
                                     code=TaskEventException.current_pomodoro_exists)

    def remove_gaps(self, task_event):
        unfinished_gaps = self.gap_selector.get_unfinished_gaps(task_event=task_event)
        unfinished_gaps.delete()

    @staticmethod
    def remove_task_event(task_event):
        if task_event is not None:
            task_event.delete()