from django.contrib import admin
from .models import Session, Exercise


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "session_type", "user"]
    list_filter = ["session_type", "date", "user"]
    search_fields = ["title", "comments"]
    inlines = [ExerciseInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["title", "session", "rest_seconds"]
    list_filter = ["session__session_type"]
    search_fields = ["title", "comments"]
