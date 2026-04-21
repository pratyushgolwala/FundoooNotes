from django.db import models
from users.models import User
from labels.models import Label


class Note(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    label = models.ForeignKey(Label, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#FFFFFF')  # Hex color code
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']  # Pinned notes first, then by date
    
    def __str__(self):
        return self.title

