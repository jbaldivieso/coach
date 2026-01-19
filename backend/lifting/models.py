from django.db import models
from django.contrib.auth.models import User


class Session(models.Model):
    """A lifting session containing multiple exercises."""

    SESSION_TYPE_CHOICES = [
        ("volume", "Volume"),
        ("weight", "Weight"),
        ("endurance", "Endurance"),
        ("recovery", "Recovery"),
    ]

    title = models.CharField(max_length=100)
    date = models.DateField()
    comments = models.TextField(blank=True)
    session_type = models.CharField(max_length=50, choices=SESSION_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lifting_sessions")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.date})"


class Exercise(models.Model):
    """An exercise within a lifting session."""

    title = models.CharField(max_length=100)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="exercises")
    weight_lbs = models.IntegerField(null=True, blank=True)
    rest_seconds = models.IntegerField()
    reps = models.JSONField()  # Array of integers like [10, 10, 8]
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.session.title}"
