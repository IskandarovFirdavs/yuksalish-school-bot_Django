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
    approved = models.BooleanField(default=False)


class StudentTaskVideo(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_videos')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)  # bu MUHIM!
    video_file = models.FileField(upload_to='student_videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.student.username} - {self.video_file.name}"


class MonthlyBook(models.Model):
    month = models.CharField(max_length=20)
    file = models.FileField(upload_to='monthly_books/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.month} - {self.file.name}"
