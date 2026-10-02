import calendar as pycal
from collections import Counter
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import forms as F
from .models import (MOODS, MOOD_INFO, WELLNESS_ACTIVITIES, Event, Goal, JournalEntry, Mood, Note, Reminder,
                     SleepRecord, Task, WaterIntake, WellnessLog, get_profile)
from .music_data import CATEGORIES, MOOD_TO_CATEGORY, songs_for


# ------------------------------------------------------------------ helpers
def pct(a, b):
    return int(round(100 * a / b)) if b else 0


def flash_errors(request, form):
    for field, errs in form.errors.items():
        label = form.fields[field].label if field in form.fields else ""
        for e in errs:
            messages.error(request, f"{label + ': ' if label else ''}{e}")


def get_ym(request):
    today = timezone.localdate()
    try:
        y, m = int(request.GET.get("y", today.year)), int(request.GET.get("m", today.month))
        if not (1 <= m <= 12 and 1900 <= y <= 2200):
            raise ValueError
    except ValueError:
        y, m = today.year, today.month
    return y, m


def ym_nav(y, m):
    prev = (y - 1, 12) if m == 1 else (y, m - 1)
    nxt = (y + 1, 1) if m == 12 else (y, m + 1)
    return {"prev": f"?y={prev[0]}&m={prev[1]}", "next": f"?y={nxt[0]}&m={nxt[1]}",
            "label": date(y, m, 1).strftime("%B %Y")}


def month_weeks(y, m):
    return pycal.Calendar(firstweekday=6).monthdatescalendar(y, m)


def parse_date(value, default=None):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return default or timezone.localdate()


def own(Model, request, pk):
    """Every object lookup is filtered by the logged-in user -> no cross-user access."""
    return get_object_or_404(Model, pk=pk, user=request.user)


def crud(Model, Form, label, url_name, created, updated, deleted, initial=None):
    """Builds add/edit and delete views for a model owned by the user."""

    @login_required
    def edit(request, pk=None):
        inst = own(Model, request, pk) if pk else None
        init = initial(request) if (initial and not inst) else None
        kwargs = {"user": request.user} if Form is F.ReminderForm else {}
        form = Form(request.POST or None, instance=inst, initial=init, **kwargs)
        if request.method == "POST":
            if form.is_valid():
                obj = form.save(commit=False)
                obj.user = request.user
                obj.save()
                messages.success(request, updated if inst else created)
                return redirect(url_name)
            flash_errors(request, form)
        return render(request, "form_page.html", {
            "form": form, "title": f"{'Edit' if inst else 'New'} {label}", "back": url_name, "obj": inst})

    @login_required
    @require_POST
    def delete(request, pk):
        own(Model, request, pk).delete()
        messages.success(request, deleted)
        return redirect(url_name)

    return edit, delete


def today_initial(request):
    return {"date": parse_date(request.GET.get("date"))}


# ------------------------------------------------------------------ auth
class DreamLoginView(LoginView):
    template_name = "login.html"
    authentication_form = F.LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        resp = super().form_valid(form)
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)  # session ends when the browser closes
        return resp


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = F.SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="core.backends.EmailOrUsernameBackend")
        messages.success(request, "Welcome to Dream Space ✨ Your little corner is ready.")
        return redirect("dashboard")
    return render(request, "signup.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You've been logged out. Come back soon 💙")
    return redirect("login")


# ------------------------------------------------------------------ dashboard
@login_required
def dashboard(request):
    u, today = request.user, timezone.localdate()
    profile = get_profile(u)
    moods = Mood.objects.filter(user=u)
    today_mood = moods.filter(date=today).order_by("-created_at").first()
    recent = moods.first()

    def avg(qs):
        s = [m.score for m in qs]
        return sum(s) / len(s) if s else None

    now = avg(moods.filter(date__gt=today - timedelta(days=7)))
    before = avg(moods.filter(date__lte=today - timedelta(days=7), date__gt=today - timedelta(days=14)))
    if now is None:
        trend = ("Log a few moods to see your trend", "·")
    elif before is None or abs(now - before) < 0.3:
        trend = ("Steady this week", "→")
    elif now > before:
        trend = ("Brighter than last week", "↗")
    else:
        trend = ("A little softer than last week", "↘")

    tasks = Task.objects.filter(user=u, date=today)
    done = tasks.filter(completed=True).count()
    water = WaterIntake.objects.filter(user=u, date=today).first()
    glasses = water.glasses if water else 0
    logged = WellnessLog.objects.filter(user=u, date=today).count()
    goals = Goal.objects.filter(user=u, status="active")
    now_dt = timezone.localtime()
    upcoming = [r for r in Reminder.objects.filter(user=u, done=False, date__gte=today)[:12]
                if (r.date, r.time) >= (today, now_dt.time()) or r.date > today][:5]

    ctx = {
        "today": today, "today_mood": today_mood, "recent_mood": recent, "trend": trend,
        "journal_count": JournalEntry.objects.filter(user=u).count(),
        "latest_journal": JournalEntry.objects.filter(user=u).first(),
        "task_total": tasks.count(), "task_done": done, "task_pending": tasks.count() - done,
        "task_pct": pct(done, tasks.count()),
        "glasses": glasses, "water_goal": profile.water_goal, "water_pct": min(100, pct(glasses, profile.water_goal)),
        "sleep": SleepRecord.objects.filter(user=u).first(),
        "wellness_done": logged, "wellness_total": len(WELLNESS_ACTIVITIES),
        "wellness_pct": pct(logged, len(WELLNESS_ACTIVITIES)),
        "goals": goals[:3], "goal_count": goals.count(),
        "reminders": upcoming,
        "events": Event.objects.filter(user=u, date__gte=today, date__lte=today + timedelta(days=14))[:4],
        "moods": MOODS,
    }
    return render(request, "dashboard.html", ctx)


# ------------------------------------------------------------------ mood
@login_required
def mood_view(request):
    u, today = request.user, timezone.localdate()
    if request.method == "POST":
        form = F.MoodForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.user = u
            m.save()
            messages.success(request, "Mood recorded 💙")
            return redirect("mood")
        flash_errors(request, form)
    all_moods = Mood.objects.filter(user=u)
    latest = {}
    for m in all_moods.order_by("created_at"):
        latest[m.date] = m
    counts = Counter(all_moods.values_list("mood", flat=True))
    most = counts.most_common(1)
    month_counts = Counter(all_moods.filter(date__gt=today - timedelta(days=30)).values_list("mood", flat=True))
    top = max(month_counts.values(), default=0)
    monthly = [{"emoji": e, "label": l, "count": month_counts.get(k, 0), "pct": pct(month_counts.get(k, 0), top)}
               for k, e, l, _ in MOODS if month_counts.get(k, 0)]
    week = [{"day": (today - timedelta(days=i)).strftime("%a"), "mood": latest.get(today - timedelta(days=i))}
            for i in range(6, -1, -1)]
    y, mo = get_ym(request)
    weeks = [[{"d": d, "in": d.month == mo, "mood": latest.get(d), "today": d == today} for d in w]
             for w in month_weeks(y, mo)]
    ctx = {
        "moods": MOODS, "today": today, "form": F.MoodForm(initial={"date": today}),
        "today_mood": all_moods.filter(date=today).first(), "history": all_moods[:30],
        "total": all_moods.count(), "most": (MOOD_INFO[most[0][0]], most[0][1]) if most else None,
        "week": week, "monthly": monthly, "weeks": weeks, "nav": ym_nav(y, mo),
    }
    return render(request, "mood.html", ctx)


@login_required
@require_POST
def mood_delete(request, pk):
    own(Mood, request, pk).delete()
    messages.success(request, "Mood entry deleted.")
    return redirect("mood")


# ------------------------------------------------------------------ journal
@login_required
def journal(request):
    qs = JournalEntry.objects.filter(user=request.user)
    q, mood = request.GET.get("q", "").strip(), request.GET.get("mood", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__icontains=q))
    if mood in MOOD_INFO:
        qs = qs.filter(mood=mood)
    return render(request, "journal.html", {"entries": qs, "q": q, "mood_filter": mood, "moods": MOODS,
                                            "total": JournalEntry.objects.filter(user=request.user).count()})


journal_edit, journal_delete = crud(
    JournalEntry, F.JournalForm, "journal entry", "journal", "Journal entry saved successfully ✨",
    "Journal entry updated ✨", "Journal entry deleted.", today_initial)


# ------------------------------------------------------------------ music
@login_required
def music(request):
    today_mood = Mood.objects.filter(user=request.user, date=timezone.localdate()).first()
    recommended = MOOD_TO_CATEGORY.get(today_mood.mood) if today_mood else None
    keys = [c[0] for c in CATEGORIES]
    cat = request.GET.get("cat")
    cat = cat if cat in keys else (recommended or "calm")
    return render(request, "music.html", {
        "categories": CATEGORIES, "cat": cat, "songs": songs_for(cat), "today_mood": today_mood,
        "recommended": recommended, "cat_label": dict((c[0], c[1]) for c in CATEGORIES)[cat]})


# ------------------------------------------------------------------ calendar
@login_required
def calendar_view(request):
    y, m = get_ym(request)
    today = timezone.localdate()
    weeks_dates = month_weeks(y, m)
    events = Event.objects.filter(user=request.user, date__gte=weeks_dates[0][0], date__lte=weeks_dates[-1][-1])
    by_day = {}
    for e in events:
        by_day.setdefault(e.date, []).append(e)
    weeks = [[{"d": d, "in": d.month == m, "today": d == today, "events": by_day.get(d, []),
               "important": any(e.is_important for e in by_day.get(d, []))} for d in w] for w in weeks_dates]
    month_events = [e for e in events if e.date.month == m and e.date.year == y]
    return render(request, "calendar.html", {"weeks": weeks, "nav": ym_nav(y, m), "month_events": month_events,
                                             "today": today})


calendar_edit, calendar_delete = crud(
    Event, F.EventForm, "event", "calendar", "Event added successfully.", "Event updated.", "Event deleted.",
    today_initial)


# ------------------------------------------------------------------ routine & reminders
@login_required
def routine(request):
    u, today = request.user, timezone.localtime()
    day = parse_date(request.GET.get("date"), today.date())
    cat = request.GET.get("cat", "")
    tasks = Task.objects.filter(user=u, date=day)
    if cat in dict(Task.CATEGORIES):
        tasks = tasks.filter(category=cat)
    tasks = list(tasks)
    done = sum(t.completed for t in tasks)
    timed = sorted([t for t in tasks if t.time], key=lambda t: t.time)
    hours = {}
    for t in timed:
        hours.setdefault(t.time.hour, []).append(t)
    timetable = [{"hour": f"{h:02d}:00", "tasks": ts} for h, ts in sorted(hours.items())]
    reminders = Reminder.objects.filter(user=u, done=False, date__gte=today.date())
    return render(request, "routine.html", {
        "tasks": tasks, "day": day, "prev": day - timedelta(days=1), "next": day + timedelta(days=1),
        "is_today": day == today.date(), "done": done, "total": len(tasks), "progress": pct(done, len(tasks)),
        "timetable": timetable, "anytime": [t for t in tasks if not t.time], "categories": Task.CATEGORIES,
        "cat": cat, "reminders": reminders})


routine_edit, routine_delete = crud(
    Task, F.TaskForm, "task", "routine", "Task added 🌿", "Task updated.", "Task deleted.", today_initial)
reminder_edit, reminder_delete = crud(
    Reminder, F.ReminderForm, "reminder", "routine", "Reminder set ⏰", "Reminder updated.", "Reminder deleted.",
    lambda r: {"date": parse_date(r.GET.get("date"))})


@login_required
@require_POST
def routine_toggle(request, pk):
    t = own(Task, request, pk)
    t.completed = not t.completed
    t.save()
    messages.success(request, "Task completed 🌿" if t.completed else "Task marked as not done.")
    return redirect(f"/routine/?date={t.date.isoformat()}")


@login_required
@require_POST
def reminder_done(request, pk):
    r = own(Reminder, request, pk)
    r.done = True
    r.save()
    messages.success(request, "Reminder done ✨")
    return redirect("routine")


# ------------------------------------------------------------------ wellness
@login_required
def wellness(request):
    u, today = request.user, timezone.localdate()
    profile = get_profile(u)
    if request.method == "POST":  # sleep form
        form = F.SleepForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            SleepRecord.objects.filter(user=u, date=d["date"]).delete()  # one record per night
            rec = form.save(commit=False)
            rec.user = u
            rec.save()
            messages.success(request, "Sleep saved 🌙")
            return redirect("wellness")
        flash_errors(request, form)
    water = WaterIntake.objects.filter(user=u, date=today).first()
    glasses = water.glasses if water else 0
    done_keys = set(WellnessLog.objects.filter(user=u, date=today).values_list("activity", flat=True))
    acts = [{"key": k, "emoji": e, "label": l, "done": k in done_keys} for k, e, l in WELLNESS_ACTIVITIES]
    sleeps = list(SleepRecord.objects.filter(user=u)[:7])
    avg = sum(float(s.duration) for s in sleeps) / len(sleeps) if sleeps else 0
    return render(request, "wellness.html", {
        "glasses": glasses, "goal": profile.water_goal, "water_pct": min(100, pct(glasses, profile.water_goal)),
        "glass_icons": range(max(profile.water_goal, glasses)), "activities": acts,
        "act_done": len(done_keys), "act_pct": pct(len(done_keys), len(acts)), "sleeps": sleeps,
        "sleep_avg": f"{avg:.1f}" if sleeps else None,
        "sleep_form": F.SleepForm(initial={"date": today, "sleep_time": "23:00", "wake_time": "07:00", "quality": 4}),
        "sleep_bars": [{"day": s.date.strftime("%a"), "h": float(s.duration), "pct": min(100, pct(float(s.duration), 10))}
                       for s in reversed(sleeps)]})


@login_required
@require_POST
def water(request):
    today = timezone.localdate()
    w, _ = WaterIntake.objects.get_or_create(user=request.user, date=today)
    if request.POST.get("action") == "add":
        w.glasses = min(30, w.glasses + 1)
        messages.success(request, "Glass added 💧")
    else:
        w.glasses = max(0, w.glasses - 1)
        messages.info(request, "Glass removed.")
    w.save()
    return redirect("wellness")


@login_required
@require_POST
def wellness_toggle(request, key):
    if key not in {k for k, _, _ in WELLNESS_ACTIVITIES}:
        return redirect("wellness")
    obj, created = WellnessLog.objects.get_or_create(user=request.user, date=timezone.localdate(), activity=key)
    if not created:
        obj.delete()
    else:
        messages.success(request, "Nice, that's one little win 🌸")
    return redirect("wellness")


@login_required
@require_POST
def sleep_delete(request, pk):
    own(SleepRecord, request, pk).delete()
    messages.success(request, "Sleep record deleted.")
    return redirect("wellness")


# ------------------------------------------------------------------ goals
@login_required
def goals(request):
    qs = Goal.objects.filter(user=request.user)
    return render(request, "goals.html", {"active": qs.exclude(status="completed"), "completed": qs.filter(status="completed")})


goals_edit, goals_delete = crud(
    Goal, F.GoalForm, "goal", "goals", "Goal created 🎯", "Goal updated.", "Goal deleted.",
    lambda r: {"start_date": timezone.localdate()})


@login_required
@require_POST
def goals_progress(request, pk):
    g = own(Goal, request, pk)
    try:
        g.progress = int(request.POST.get("progress", g.progress))
    except ValueError:
        messages.error(request, "Progress must be a number between 0 and 100.")
        return redirect("goals")
    g.save()
    messages.success(request, "Goal completed. Beautiful work 🎉" if g.status == "completed" else "Progress updated 🌱")
    return redirect("goals")


# ------------------------------------------------------------------ notes
@login_required
def notes(request):
    qs = Note.objects.filter(user=request.user)
    q, cat = request.GET.get("q", "").strip(), request.GET.get("cat", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if cat in dict(Note.CATEGORIES):
        qs = qs.filter(category=cat)
    return render(request, "notes.html", {"notes": qs, "q": q, "cat": cat, "categories": Note.CATEGORIES,
                                          "total": Note.objects.filter(user=request.user).count()})


notes_edit, notes_delete = crud(Note, F.NoteForm, "note", "notes", "Note saved ✨", "Note updated.", "Note deleted.")


# ------------------------------------------------------------------ settings
@login_required
def settings_view(request):
    user = request.user
    profile = get_profile(user)
    pf, pw, pr = F.ProfileForm(instance=user), F.StyledPasswordChangeForm(user), F.PrefsForm(instance=profile)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            pf = F.ProfileForm(request.POST, instance=user)
            if pf.is_valid():
                pf.save()
                messages.success(request, "Profile updated ✨")
                return redirect("settings")
            flash_errors(request, pf)
        elif action == "password":
            pw = F.StyledPasswordChangeForm(user, request.POST)
            if pw.is_valid():
                user = pw.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully 🔒")
                return redirect("settings")
            flash_errors(request, pw)
        elif action == "prefs":
            pr = F.PrefsForm(request.POST, instance=profile)
            if pr.is_valid():
                pr.save()
                messages.success(request, "Preferences saved 🌿")
                return redirect("settings")
            flash_errors(request, pr)
        elif action == "delete":
            if user.check_password(request.POST.get("password", "")):
                logout(request)
                user.delete()  # cascades to all of the user's data
                messages.success(request, "Your account and all its data have been deleted.")
                return redirect("login")
            messages.error(request, "That password isn't correct, so your account was not deleted.")
    return render(request, "settings.html", {"pf": pf, "pw": pw, "pr": pr})
