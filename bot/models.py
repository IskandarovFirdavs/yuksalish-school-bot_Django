from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('curator', 'Curator'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True)
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True)
    student_class = models.ForeignKey("StudentClass", on_delete=models.SET_NULL, null=True, blank=True)

class Branch(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class StudentClass(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

class VideoSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    video = models.FileField(upload_to='videos/')
    submitted_at = models.DateTimeField(auto_now_add=True)
