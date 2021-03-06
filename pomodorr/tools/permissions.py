from django.utils.translation import gettext_lazy as _
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated


class IsObjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsNotAuthenticated(IsAuthenticated):
    message = _("Only unauthenticated users are allowed to perform this action.")

    def has_permission(self, request, view):
        return not request.user.is_authenticated


class IsTaskOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.project.user == request.user


class IsSubTaskOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.task.project.user == request.user


class IsDateFrameOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.task.project.user == request.user
