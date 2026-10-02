from django.contrib import admin

from . import models

for m in (models.Mood, models.JournalEntry, models.Event, models.Task, models.Reminder, models.WaterIntake,
          models.SleepRecord, models.WellnessLog, models.Goal, models.Note, models.Profile):
    admin.site.register(m)
