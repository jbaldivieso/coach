from django.db import models
from django.contrib.auth.models import User


class Session(models.Model):
    """A lifting session containing multiple exercises."""

    STATUS_PLANNED = "planned"
    STATUS_ACTIVE = "active"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_PLANNED, "Planned"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_DONE, "Done"),
    ]

    title = models.CharField(max_length=100)
    date = models.DateField()
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DONE)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lifting_sessions")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.title} ({self.date})"


class Exercise(models.Model):
    """An exercise within a lifting session.

    Adjacent exercises sharing a superset_group form a superset; the group's
    rest comes from its first exercise.
    """

    title = models.CharField(max_length=100)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="exercises")
    sets = models.JSONField(default=list)  # [{"weight": float|null, "reps": int, "done": bool}]
    rest_seconds = models.IntegerField()
    comments = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)
    superset_group = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.title} - {self.session.title}"
