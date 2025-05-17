from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Branch, StudentClass, Task, VideoSubmission, MonthlyBook


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "first_name", "role", "branch", "student_class", "is_staff")
    list_filter = ("role", "branch", "student_class", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role', 'branch', 'student_class')}),
    )

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)

@admin.register(VideoSubmission)
class VideoSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "submitted_at")
    list_filter = ("submitted_at",)

from django.contrib import admin
from .models import StudentTaskVideo

@admin.register(StudentTaskVideo)
class StudentTaskVideoAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'video_file', 'uploaded_at')
    search_fields = ('student__username', 'task__title')
    list_filter = ('uploaded_at', 'task')

@admin.register(MonthlyBook)
class MonthlyBookAdmin(admin.ModelAdmin):
    list_display = ['month', 'uploaded_at', 'uploaded_by']