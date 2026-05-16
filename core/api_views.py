from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

from .models import Project, Task, User
from .serializers import ProjectSerializer, TaskSerializer, UserSerializer


class IsAdminUserRole(permissions.BasePermission):
    """Only allow users with role='admin' to write."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_admin()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminUserRole]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Project.objects.filter(
                Q(created_by=user) | Q(members=user)
            ).distinct()
        return Project.objects.filter(members=user).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Task.objects.filter(
                Q(project__created_by=user) | Q(project__members=user)
            ).distinct()
        return Task.objects.filter(assigned_to=user)

    def perform_create(self, serializer):
        if not self.request.user.is_admin():
            return Response(
                {'detail': 'Only admins can create tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        # Members can only update status of their own tasks
        if not request.user.is_admin():
            allowed_fields = {'status'}
            if not set(request.data.keys()).issubset(allowed_fields):
                return Response(
                    {'detail': 'Members can only update task status.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if task.assigned_to_id != request.user.id:
                return Response(
                    {'detail': 'You can only update tasks assigned to you.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin():
            return Response(
                {'detail': 'Only admins can delete tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class UserListViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of users for assigning tasks."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
