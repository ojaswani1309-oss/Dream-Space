from django.utils import timezone

from .models import Reminder, get_profile


def reminders(request):
    """Feeds the browser-notification script (only if the user enabled it)."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    profile = get_profile(user)
    if not profile.notify_browser:
        return {"browser_reminders": []}
    today = timezone.localdate()
    items = Reminder.objects.filter(user=user, done=False, date=today)
    return {"browser_reminders": [
        {"id": r.id, "title": r.title, "time": r.time.strftime("%H:%M")} for r in items]}
