from django.contrib import admin
from .models import Session, Exercise, Template, TemplateExercise


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


class TemplateExerciseInline(admin.TabularInline):
    model = TemplateExercise
    extra = 1


class ArchivedFilter(admin.SimpleListFilter):
    title = "archived"
    parameter_name = "archived"

    def lookups(self, request, model_admin):
        return [("yes", "Yes"), ("no", "No")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(archived_at__isnull=False)
        if self.value() == "no":
            return queryset.filter(archived_at__isnull=True)
        return queryset


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ["title", "updated_at", "archived_at", "user"]
    list_filter = [ArchivedFilter, "user"]
    search_fields = ["title", "comments"]
    inlines = [TemplateExerciseInline]
