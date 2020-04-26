from datetime import timedelta

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from pomodorr.projects.exceptions import ProjectException, PriorityException, TaskException, SubTaskException
from pomodorr.projects.models import Project, Priority, Task, SubTask
from pomodorr.projects.selectors import PrioritySelector, ProjectSelector, TaskSelector
from pomodorr.projects.services import TaskServiceModel, ProjectServiceModel, SubTaskServiceModel
from pomodorr.tools.utils import has_changed
from pomodorr.tools.validators import duration_validator, today_validator
from pomodorr.users.services import UserDomainModel


class PrioritySerializer(serializers.ModelSerializer):
    priority_level = serializers.IntegerField(required=True, min_value=1)
    user = serializers.PrimaryKeyRelatedField(write_only=True, default=serializers.CurrentUserDefault(),
                                              queryset=UserDomainModel.get_active_standard_users())

    def validate(self, data):
        self.check_priority_name_uniqueness(data=data)
        return data

    def check_priority_name_uniqueness(self, data):
        user = self.context['request'].user
        name = data.get('name') or None

        if name is not None and PrioritySelector.get_priorities_for_user(user=user, name=name).exists():
            raise serializers.ValidationError(
                {'name': PriorityException.messages[PriorityException.priority_duplicated]},
                code=PriorityException.priority_duplicated)
        return data

    class Meta:
        model = Priority
        fields = ('id', 'name', 'priority_level', 'color', 'user')


class ProjectSerializer(ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(write_only=True, default=serializers.CurrentUserDefault(),
                                              queryset=UserDomainModel.get_active_standard_users())
    priority = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=PrioritySelector.get_all_priorities())
    user_defined_ordering = serializers.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        super(ProjectSerializer, self).__init__(*args, **kwargs)
        self.service_model = ProjectServiceModel

    def validate_priority(self, value):
        user = self.context['request'].user

        if not PrioritySelector.get_priorities_for_user(user=user).filter(id=value.id).exists():
            raise serializers.ValidationError(ProjectException.messages[ProjectException.priority_does_not_exist],
                                              code=ProjectException.priority_does_not_exist)
        return value

    def validate(self, data):
        #  Temporary solution for https://github.com/encode/django-rest-framework/issues/7100
        self.check_project_name_uniqueness(data=data)
        return data

    def check_project_name_uniqueness(self, data):
        user = self.context['request'].user
        name = data.get('name') or None

        if user is not None and name is not None and not self.service_model.is_project_name_available(
            user=user, name=name, exclude=self.instance):
            raise serializers.ValidationError(
                {'name': ProjectException.messages[ProjectException.project_duplicated]},
                code=ProjectException.project_duplicated)

    # todo: priority should be represented with whole priority - not only id
    class Meta:
        model = Project
        fields = ('id', 'name', 'priority', 'user_defined_ordering', 'user')


class TaskSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=ProjectSelector.get_all_active_projects()
    )
    priority = serializers.PrimaryKeyRelatedField(
        required=False, allow_empty=True, allow_null=True,
        queryset=PrioritySelector.get_all_priorities()
    )
    user_defined_ordering = serializers.IntegerField(min_value=1)
    pomodoro_length = serializers.DurationField(required=False, allow_null=True, min_value=timedelta(minutes=5),
                                                max_value=timedelta(hours=6))
    repeat_duration = serializers.DurationField(required=False, allow_null=True, min_value=timedelta(days=1),
                                                validators=[duration_validator])
    due_date = serializers.DateTimeField(required=False, allow_null=True, validators=[today_validator])

    def __init__(self, *args, **kwargs):
        super(TaskSerializer, self).__init__(*args, **kwargs)
        self.service_model = TaskServiceModel()

    def validate_project(self, value):
        user = self.context['request'].user

        if not ProjectSelector.get_active_projects_for_user(user=user, id=value.id).exists():
            raise serializers.ValidationError(TaskException.messages[TaskException.project_does_not_exist],
                                              code=TaskException.project_does_not_exist)
        return value

    def validate_priority(self, value):
        user = self.context['request'].user

        if value and not PrioritySelector.get_priorities_for_user(user=user).filter(id=value.id).exists():
            raise serializers.ValidationError(TaskException.messages[TaskException.priority_does_not_exist],
                                              code=TaskException.priority_does_not_exist)
        return value

    def validate_status(self, value):
        if not self.instance and value and value == self.Meta.model.status_completed:
            raise serializers.ValidationError(TaskException.messages[TaskException.wrong_status],
                                              code=TaskException.wrong_status)
        return value

    def update(self, instance, validated_data):
        status = validated_data.pop('status') if 'status' in validated_data else None
        project = validated_data.pop('project') if 'project' in validated_data else None

        if status is not None:
            if has_changed(instance, 'status', status, self.Meta.model.status_completed):
                instance = self.service_model.complete_task(task=self.instance, db_save=False)
            elif has_changed(instance, 'status', status, self.Meta.model.status_active):
                instance = self.service_model.reactivate_task(task=self.instance, db_save=False)

        if project is not None and has_changed(instance, 'project', project):
            instance = self.service_model.pin_to_project(task=instance, project=project, db_save=False)

        return super(TaskSerializer, self).update(instance, validated_data)

    def validate(self, data):
        # Temporary solution for https://github.com/encode/django-rest-framework/issues/7100
        self.check_task_name_uniqueness(data=data)
        return data

    def check_task_name_uniqueness(self, data):
        name = data.get('name') or None
        project = data.get('project') or None

        if name is not None and project is not None and not self.service_model.is_task_name_available(
            project=project, name=name, exclude=self.instance):
            raise serializers.ValidationError({'name': TaskException.messages[TaskException.task_duplicated]},
                                              code=TaskException.task_duplicated)

    class Meta:
        model = Task
        fields = (
            'id', 'name', 'status', 'project', 'priority', 'user_defined_ordering', 'pomodoro_number',
            'pomodoro_length', 'due_date', 'reminder_date', 'repeat_duration', 'note')

    def to_representation(self, instance):
        data = super(TaskSerializer, self).to_representation(instance=instance)
        data['status'] = instance.get_status_display()
        return data


class SubTaskSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=TaskSelector.get_all_non_removed_tasks()
    )

    def __init__(self, *args, **kwargs):
        super(SubTaskSerializer, self).__init__(*args, **kwargs)
        self.service_model = SubTaskServiceModel()

    class Meta:
        model = SubTask
        fields = ('name', 'task', 'is_completed')

    def validate_task(self, value):
        user = self.context['request'].user

        if value and not TaskSelector.get_all_non_removed_tasks_for_user(user=user, id=value.id).exists():
            raise serializers.ValidationError(SubTaskException.messages[SubTaskException.task_does_not_exist],
                                              code=SubTaskException.task_does_not_exist)

        if value and value.status == Task.status_completed:
            raise serializers.ValidationError(SubTaskException.messages[SubTaskException.task_already_completed],
                                              code=SubTaskException.task_already_completed)

        if self.instance and has_changed(self.instance, 'task', value):
            raise serializers.ValidationError(SubTaskException.messages[SubTaskException.cannot_change_task],
                                              code=SubTaskException.cannot_change_task)

        return value

    def validate(self, data):
        self.check_sub_task_name_uniqueness(data=data)
        return data

    def check_sub_task_name_uniqueness(self, data):
        name = data.get('name') or None
        task = data.get('task') or None
        user = self.context['request'].user

        if name is not None and task is not None and user is not None and \
            not self.service_model.is_sub_task_name_available(task=task, name=name, exclude=self.instance):
            raise serializers.ValidationError(
                {'name': [SubTaskException.messages[SubTaskException.sub_task_duplicated]]},
                code=SubTaskException.sub_task_duplicated)

# todo: instead of hooking the domain logic into the update method of the serializer - stub it into models so the admin
# todo: panel will ass well be able to use it
