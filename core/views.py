from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from functools import wraps

from .models import User, Project, Task
from .forms import SignUpForm, ProjectForm, TaskForm, TaskStatusForm


# ---------- Helpers ----------

def admin_required(view_func):
    """Block non-admins from admin-only views."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin():
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def user_can_view_project(user, project):
    """A user can see a project if they own it OR are a member."""
    return project.created_by_id == user.id or project.members.filter(id=user.id).exists()


# ---------- Auth ----------

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- Dashboard ----------

@login_required
def dashboard(request):
    user = request.user
    if user.is_admin():
        projects = Project.objects.filter(
            Q(created_by=user) | Q(members=user)
        ).distinct()
    else:
        projects = Project.objects.filter(members=user).distinct()

    my_tasks = Task.objects.filter(assigned_to=user).select_related('project')

    today = timezone.now().date()
    overdue_tasks = my_tasks.filter(due_date__lt=today).exclude(status=Task.STATUS_DONE)

    stats = {
        'total_projects': projects.count(),
        'total_tasks': my_tasks.count(),
        'todo': my_tasks.filter(status=Task.STATUS_TODO).count(),
        'in_progress': my_tasks.filter(status=Task.STATUS_IN_PROGRESS).count(),
        'done': my_tasks.filter(status=Task.STATUS_DONE).count(),
        'overdue': overdue_tasks.count(),
    }

    return render(request, 'core/dashboard.html', {
        'projects': projects,
        'my_tasks': my_tasks[:10],
        'overdue_tasks': overdue_tasks,
        'stats': stats,
    })


# ---------- Projects ----------

@login_required
def project_list(request):
    user = request.user
    if user.is_admin():
        projects = Project.objects.filter(
            Q(created_by=user) | Q(members=user)
        ).distinct()
    else:
        projects = Project.objects.filter(members=user).distinct()
    return render(request, 'core/project_list.html', {'projects': projects})


@admin_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()
            messages.success(request, f'Project "{project.name}" created.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'core/project_form.html', {'form': form, 'action': 'Create'})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not user_can_view_project(request.user, project):
        return HttpResponseForbidden('You do not have access to this project.')
    tasks = project.tasks.select_related('assigned_to').all()

    # Members only see their own tasks; admins see all
    if not request.user.is_admin():
        tasks = tasks.filter(assigned_to=request.user)

    return render(request, 'core/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'stats': project.task_stats(),
        'is_owner': project.created_by_id == request.user.id,
    })


@admin_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.created_by_id != request.user.id:
        return HttpResponseForbidden('Only the project creator can edit it.')
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'core/project_form.html', {
        'form': form, 'action': 'Edit', 'project': project,
    })


@admin_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.created_by_id != request.user.id:
        return HttpResponseForbidden('Only the project creator can delete it.')
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted.')
        return redirect('project_list')
    return render(request, 'core/project_confirm_delete.html', {'project': project})


# ---------- Tasks ----------

@admin_required
def task_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not user_can_view_project(request.user, project):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = TaskForm(project=project)
    return render(request, 'core/task_form.html', {
        'form': form, 'project': project, 'action': 'Create',
    })


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if not user_can_view_project(request.user, project):
        return HttpResponseForbidden()

    can_edit_full = request.user.is_admin() and project.created_by_id == request.user.id
    can_update_status = (
        task.assigned_to_id == request.user.id or can_edit_full
    )

    if request.method == 'POST' and can_update_status and not can_edit_full:
        form = TaskStatusForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Status updated.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskStatusForm(instance=task)

    return render(request, 'core/task_detail.html', {
        'task': task,
        'project': project,
        'status_form': form,
        'can_edit_full': can_edit_full,
        'can_update_status': can_update_status,
    })


@admin_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if project.created_by_id != request.user.id:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, project=project)
    return render(request, 'core/task_form.html', {
        'form': form, 'project': project, 'action': 'Edit', 'task': task,
    })


@admin_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if project.created_by_id != request.user.id:
        return HttpResponseForbidden()
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'core/task_confirm_delete.html', {'task': task})
