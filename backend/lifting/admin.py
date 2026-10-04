from django.contrib import admin
from .models import Session, Exercise


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "status", "user"]
    list_filter = ["status", "date", "user"]
    search_fields = ["title", "comments"]
    inlines = [ExerciseInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["title", "session", "rest_seconds", "superset_group"]
    list_filter = ["session__status"]
    search_fields = ["title", "comments"]
