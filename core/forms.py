from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Project, Task


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial=User.ROLE_MEMBER,
        help_text='Admins can create projects and assign tasks. Members can only update their assigned tasks.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')


class ProjectForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text='Select team members for this project.'
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'members']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            # Restrict assignee dropdown to project members + creator
            member_ids = list(project.members.values_list('id', flat=True))
            member_ids.append(project.created_by.id)
            self.fields['assigned_to'].queryset = User.objects.filter(id__in=member_ids)


class TaskStatusForm(forms.ModelForm):
    """Lightweight form for members to update only the status of their tasks."""
    class Meta:
        model = Task
        fields = ['status']
