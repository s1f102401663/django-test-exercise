from django.db import models
from django.utils import timezone


# Create your models here.
class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    ]
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    posted_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
    )
    memo = models.TextField(blank=True)
    comment = models.TextField(blank=True, null=True)

    def is_overdue(self, dt):
        if self.due_at is None:
            return False
        return self.due_at < dt
    
    def __str__(self):
        return self.title
