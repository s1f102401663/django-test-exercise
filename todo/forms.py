from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'due_at', 'priority', 'Comment']
        widgets = {
            'due_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
             }