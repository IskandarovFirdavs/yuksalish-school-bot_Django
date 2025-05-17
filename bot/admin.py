from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Branch, StudentClass, Task, VideoSubmission

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
