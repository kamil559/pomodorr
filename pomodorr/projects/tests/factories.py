import random
from datetime import timedelta

import factory
from django.utils import timezone
from factory.fuzzy import FuzzyAttribute

from pomodorr.projects.models import Project, Priority, Task, SubTask, TaskEvent, Gap
from pomodorr.tools.utils import get_time_delta


class PriorityFactory(factory.DjangoModelFactory):
    priority_level = FuzzyAttribute(lambda: random.randint(1, 10))
    name = factory.LazyAttributeSequence(lambda o, n: f'{n} Priority level: {o.priority_level}')
    color = factory.Faker('color')

    class Meta:
        model = Priority


class ProjectFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Project number: {n}')
    user_defined_ordering = FuzzyAttribute(lambda: random.randint(1, 50))

    class Meta:
        model = Project


class TaskFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Task: {n}')
    user_defined_ordering = FuzzyAttribute(lambda: random.randint(1, 50))
    pomodoro_number = FuzzyAttribute(lambda: random.randint(1, 50))
    pomodoro_length = FuzzyAttribute(lambda: timedelta(minutes=25))
    note = factory.Faker('text')

    class Meta:
        model = Task


class SubTaskFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'SubTask {n}')
    is_completed = FuzzyAttribute(lambda: bool(random.randint(0, 1)))

    class Meta:
        model = SubTask


class TaskEventFactory(factory.DjangoModelFactory):
    start = factory.LazyFunction(timezone.now)
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=25))

    class Meta:
        model = TaskEvent


class GapFactory(factory.DjangoModelFactory):
    start = factory.Sequence(lambda n: get_time_delta({'minutes': n * 3}))
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=1))

    class Meta:
        model = Gap