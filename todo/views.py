from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task
from .forms import TaskForm

# Create your views here.
def index(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = TaskForm()

    tasks = Task.objects.all()

    filter_param = request.GET.get('filter')
    if filter_param == 'complete':
        tasks = tasks.filter(completed=True)
    elif filter_param == 'incomplete':
        tasks = tasks.filter(completed=False)

    query = request.GET.get('q')
    if query:
        tasks = tasks.filter(title__icontains=query)

    order_param = request.GET.get('order')
    if order_param == 'due':
        tasks = tasks.order_by('due_at')
    elif order_param == 'priority':
        tasks = tasks.order_by('-priority')
    else:
        tasks = tasks.order_by('-posted_at')

    context = {
        'tasks': tasks,
        'form': form
    }
    return render(request, 'todo/index.html', context)


def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    
    if request.method == 'POST':
        task.memo = request.POST.get('memo', '')
        task.save()
        return redirect('detail', task_id=task.id)

    context = {
        'task': task
    }
    return render(request, 'todo/detail.html', context)

def update(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('detail', task_id=task.pk)
    else:
        form = TaskForm(instance=task)

    context = {
        'task': task,
        'form': form
    }
    return render(request, "todo/edit.html", context)

def delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id) 
    task.delete()
    return redirect(index)

def complete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.completed = not task.completed
    task.save()
    return redirect('index')