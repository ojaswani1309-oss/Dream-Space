from datetime import datetime, timedelta

from django.conf import settings
from django.db import models

# (key, emoji, label, score used for the mood trend)
MOODS = [
    ("happy", "😊", "Happy", 5), ("calm", "😌", "Calm", 4), ("loved", "🥰", "Loved", 5),
    ("excited", "😄", "Excited", 5), ("good", "🙂", "Good", 4), ("neutral", "😐", "Neutral", 3),
    ("sad", "😔", "Sad", 1), ("anxious", "😟", "Anxious", 2), ("angry", "😡", "Angry", 1),
    ("tired", "😴", "Tired", 2),
]
MOOD_CHOICES = [(k, f"{e} {l}") for k, e, l, _ in MOODS]
MOOD_INFO = {k: {"emoji": e, "label": l, "score": s} for k, e, l, s in MOODS}

WELLNESS_ACTIVITIES = [
    ("water", "💧", "Drink water"), ("sleep", "🌙", "Sleep well"), ("break", "☕", "Take a break"),
    ("exercise", "🏃‍♀️", "Exercise"), ("read", "📖", "Read"), ("meditate", "🧘", "Meditation"),
    ("selfcare", "🌸", "Self-care"),
]

User = settings.AUTH_USER_MODEL


class MoodMixin:
    @property
    def emoji(self):
        return MOOD_INFO.get(self.mood, {}).get("emoji", "")

    @property
    def label(self):
        return MOOD_INFO.get(self.mood, {}).get("label", "")

    @property
    def score(self):
        return MOOD_INFO.get(self.mood, {}).get("score", 3)


class Mood(MoodMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="moods")
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    reason = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    note = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.user} {self.mood} {self.date}"


class JournalEntry(MoodMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="journal_entries")
    title = models.CharField(max_length=200)
    content = models.TextField()
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Separate tags with commas")
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name_plural = "journal entries"

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def __str__(self):
        return self.title


class Event(models.Model):
    CATEGORIES = [("personal", "Personal"), ("study", "Study"), ("work", "Work"), ("birthday", "Birthday"),
                  ("important", "Important"), ("self_care", "Self-care")]
    REMINDERS = [("none", "No reminder"), ("15", "15 minutes before"), ("60", "1 hour before"),
                 ("1440", "1 day before")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="personal")
    reminder = models.CharField(max_length=10, choices=REMINDERS, default="none")
    is_important = models.BooleanField("Mark as important date", default=False)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return self.title


class Task(models.Model):
    CATEGORIES = [("morning", "Morning"), ("study", "Study"), ("work", "Work"), ("exercise", "Exercise"),
                  ("self_care", "Self-care"), ("evening", "Evening"), ("sleep", "Sleep")]
    PRIORITIES = [("low", "Low"), ("medium", "Medium"), ("high", "High")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField("Task name", max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="morning")
    priority = models.CharField(max_length=10, choices=PRIORITIES, default="medium")
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "time", "id"]

    def __str__(self):
        return self.title


class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reminders")
    title = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField()
    task = models.ForeignKey(Task, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="reminders", verbose_name="Related task")
    done = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return self.title


class WaterIntake(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="water")
    date = models.DateField()
    glasses = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")


class SleepRecord(models.Model):
    QUALITY = [(1, "1 – Restless"), (2, "2 – Poor"), (3, "3 – Okay"), (4, "4 – Good"), (5, "5 – Dreamy")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sleep_records")
    date = models.DateField("Wake-up date")
    sleep_time = models.TimeField("Went to bed")
    wake_time = models.TimeField("Woke up")
    duration = models.DecimalField(max_digits=4, decimal_places=2, default=0)  # hours
    quality = models.PositiveSmallIntegerField(choices=QUALITY, default=3)

    class Meta:
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        start = datetime.combine(self.date, self.sleep_time)
        end = datetime.combine(self.date, self.wake_time)
        if end <= start:
            end += timedelta(days=1)
        self.duration = round((end - start).total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    @property
    def duration_text(self):
        total = int(round(float(self.duration) * 60))
        return f"{total // 60}h {total % 60:02d}m"


class WellnessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wellness_logs")
    date = models.DateField()
    activity = models.CharField(max_length=20)

    class Meta:
        unique_together = ("user", "date", "activity")


class Goal(models.Model):
    STATUSES = [("active", "Active"), ("paused", "Paused"), ("completed", "Completed")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    target_date = models.DateField(null=True, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUSES, default="active")

    class Meta:
        ordering = ["target_date", "id"]

    def save(self, *args, **kwargs):
        self.progress = max(0, min(100, self.progress))
        if self.progress >= 100:
            self.status = "completed"
        elif self.status == "completed":
            self.status = "active"
        super().save(*args, **kwargs)


class Note(models.Model):
    CATEGORIES = [("personal", "Personal"), ("study", "Study"), ("ideas", "Ideas"),
                  ("important", "Important"), ("memories", "Memories")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class Profile(models.Model):
    LEADS = [(0, "At the time"), (10, "10 minutes before"), (30, "30 minutes before"), (60, "1 hour before")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    notify_email = models.BooleanField("Email me about reminders", default=False)
    notify_browser = models.BooleanField("Browser notifications", default=False)
    reminder_lead = models.PositiveSmallIntegerField("Default reminder", choices=LEADS, default=10)
    water_goal = models.PositiveSmallIntegerField("Daily water goal (glasses)", default=8)


def get_profile(user):
    return Profile.objects.get_or_create(user=user)[0]
