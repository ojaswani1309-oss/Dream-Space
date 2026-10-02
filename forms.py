from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password

from .models import (Event, Goal, JournalEntry, Mood, Note, Profile, Reminder, SleepRecord, Task)

User = get_user_model()
DATE = lambda: forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")  # noqa: E731
TIME = lambda: forms.TimeInput(attrs={"type": "time"}, format="%H:%M")  # noqa: E731


class Styled:
    """Adds CSS classes to every widget."""

    def style(self):
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, (forms.CheckboxInput,)):
                w.attrs["class"] = "check"
            else:
                w.attrs["class"] = (w.attrs.get("class", "") + " input").strip()


class StyledForm(Styled, forms.Form):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style()


class StyledModelForm(Styled, forms.ModelForm):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style()


# ---------- auth ----------
class LoginForm(Styled, AuthenticationForm):
    username = forms.CharField(label="Email or username",
                               widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "you@example.com"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Your password"}))
    remember_me = forms.BooleanField(required=False, label="Remember me")
    error_messages = {"invalid_login": "That email/username and password don't match. Please try again.",
                      "inactive": "This account is inactive."}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style()


class SignUpForm(StyledForm):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"placeholder": "Your full name"}))
    username = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder": "Pick a username"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"placeholder": "At least 8 characters"}))
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"}))

    def clean_username(self):
        u = self.cleaned_data["username"].strip()
        if not u.replace("_", "").replace(".", "").replace("-", "").isalnum():
            raise forms.ValidationError("Use only letters, numbers, dots, dashes and underscores.")
        if User.objects.filter(username__iexact=u).exists():
            raise forms.ValidationError("That username is already taken.")
        return u

    def clean_email(self):
        e = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=e).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return e

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords don't match.")
        elif p1:
            try:
                validate_password(p1, User(username=data.get("username", ""), email=data.get("email", "")))
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return data

    def save(self):
        d = self.cleaned_data
        return User.objects.create_user(username=d["username"], email=d["email"], password=d["password1"],
                                        first_name=d["full_name"].strip())


# ---------- settings ----------
class ProfileForm(StyledModelForm):
    first_name = forms.CharField(label="Full name", max_length=150)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["first_name", "username", "email"]

    def clean_email(self):
        e = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=e).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("That email is used by another account.")
        return e


class PrefsForm(StyledModelForm):
    class Meta:
        model = Profile
        fields = ["notify_browser", "notify_email", "reminder_lead", "water_goal"]
        widgets = {"water_goal": forms.NumberInput(attrs={"min": 1, "max": 20})}


class StyledPasswordChangeForm(Styled, PasswordChangeForm):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style()


# ---------- content ----------
class MoodForm(StyledModelForm):
    class Meta:
        model = Mood
        fields = ["mood", "reason", "description", "note", "date"]
        widgets = {"date": DATE(), "description": forms.Textarea(attrs={"rows": 2}),
                   "note": forms.Textarea(attrs={"rows": 2})}


class JournalForm(StyledModelForm):
    class Meta:
        model = JournalEntry
        fields = ["title", "date", "mood", "content", "tags"]
        widgets = {"date": DATE(), "content": forms.Textarea(attrs={"rows": 12, "placeholder": "Dear journal…"}),
                   "tags": forms.TextInput(attrs={"placeholder": "gratitude, friends, growth"})}


class EventForm(StyledModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "date", "time", "category", "reminder", "is_important"]
        widgets = {"date": DATE(), "time": TIME(), "description": forms.Textarea(attrs={"rows": 3})}


class TaskForm(StyledModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "date", "time", "category", "priority", "completed"]
        widgets = {"date": DATE(), "time": TIME(), "description": forms.Textarea(attrs={"rows": 3})}


class ReminderForm(StyledModelForm):
    def __init__(self, *a, user=None, **kw):
        super().__init__(*a, **kw)
        self.fields["task"].queryset = Task.objects.filter(user=user) if user else Task.objects.none()
        self.fields["task"].required = False

    class Meta:
        model = Reminder
        fields = ["title", "date", "time", "task", "done"]
        labels = {"done": "Already done"}
        widgets = {"date": DATE(), "time": TIME()}


class SleepForm(StyledModelForm):
    class Meta:
        model = SleepRecord
        fields = ["date", "sleep_time", "wake_time", "quality"]
        widgets = {"date": DATE(), "sleep_time": TIME(), "wake_time": TIME()}


class GoalForm(StyledModelForm):
    class Meta:
        model = Goal
        fields = ["title", "description", "start_date", "target_date", "progress", "status"]
        widgets = {"start_date": DATE(), "target_date": DATE(), "description": forms.Textarea(attrs={"rows": 3}),
                   "progress": forms.NumberInput(attrs={"min": 0, "max": 100})}


class NoteForm(StyledModelForm):
    class Meta:
        model = Note
        fields = ["title", "category", "content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 8})}
