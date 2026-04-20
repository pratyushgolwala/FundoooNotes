from django.db import models
from users.models import User


class Label(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="labels")
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

