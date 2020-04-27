from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from pomodorr.projects.selectors import ProjectSelector, PrioritySelector, TaskSelector, SubTaskSelector
from pomodorr.projects.serializers import ProjectSerializer, PrioritySerializer, TaskSerializer, SubTaskSerializer
from pomodorr.tools.permissions import IsObjectOwner, IsTaskOwner, IsSubTaskOwner


class PriorityViewSet(ModelViewSet):
    queryset = PrioritySelector.get_all_priorities()
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = PrioritySerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'priority_level', 'name']
    filterset_fields = {
        'priority_level': ['exact', 'gt', 'gte', 'lt', 'lte'],
        'name': ['exact', 'iexact', 'contains', 'icontains']
    }

    def get_queryset(self):
        return PrioritySelector.get_priorities_for_user(user=self.request.user)

    def get_serializer_context(self):
        return dict(request=self.request)


class ProjectsViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = ProjectSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'priority__priority_level', 'user_defined_ordering', 'name']
    filterset_fields = {
        'priority__priority_level': ['exact', 'gt', 'gte', 'lt', 'lte'],
        'name': ['exact', 'iexact', 'contains', 'icontains']
    }

    def get_queryset(self):
        return ProjectSelector.get_active_projects_for_user(user=self.request.user)

    def get_serializer_context(self) -> dict:
        return dict(request=self.request)


class TaskViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsAuthenticated, IsTaskOwner)
    serializer_class = TaskSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'priority__priority_level', 'user_defined_ordering', 'name']
    filterset_fields = {
        'priority__priority_level': ['exact', 'gt', 'gte', 'lt', 'lte'],
        'name': ['exact', 'iexact', 'contains', 'icontains'],
        'project__id': ['exact']
    }

    def get_queryset(self):
        return TaskSelector.get_all_non_removed_tasks_for_user(user=self.request.user)

    def get_serializer_context(self):
        return dict(request=self.request)


class SubTaskViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsAuthenticated, IsSubTaskOwner)
    serializer_class = SubTaskSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'name', 'is_completed']
    filterset_fields = {
        'name': ['exact', 'iexact', 'contains', 'icontains'],
        'is_completed': ['exact'],
        'task__id': ['exact']
    }

    def get_queryset(self):
        return SubTaskSelector.get_all_sub_tasks_for_user(user=self.request.user)

    def get_serializer_context(self):
        return dict(request=self.request)
