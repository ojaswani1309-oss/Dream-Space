from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Goal, JournalEntry, Mood, Note, SleepRecord, Task

User = get_user_model()
PAGES = ["dashboard", "mood", "journal", "journal_add", "music", "calendar", "calendar_add", "routine",
         "routine_add", "routine_reminder_add", "wellness", "goals", "goals_add", "notes", "notes_add", "settings"]


class DreamSpaceTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user("alice", "a@x.com", "S3cure!pass99", first_name="Alice")
        self.b = User.objects.create_user("bob", "b@x.com", "S3cure!pass99", first_name="Bob")

    def test_login_required(self):
        for name in PAGES:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn("/login/", r["Location"])

    def test_all_pages_render(self):
        self.client.login(username="alice", password="S3cure!pass99")
        for name in PAGES:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        for cat in ("happy", "sleep"):
            self.assertEqual(self.client.get(reverse("music"), {"cat": cat}).status_code, 200)

    def test_login_with_email_and_signup(self):
        self.assertTrue(self.client.login(username="a@x.com", password="S3cure!pass99"))
        self.client.logout()
        r = self.client.post(reverse("signup"), {"full_name": "Cara", "username": "cara", "email": "c@x.com",
                                                 "password1": "Tr1cky!pass77", "password2": "Tr1cky!pass77"})
        self.assertRedirects(r, reverse("dashboard"))
        r = self.client.post(reverse("logout"))
        r = self.client.post(reverse("signup"), {"full_name": "D", "username": "alice", "email": "a@x.com",
                                                 "password1": "abc", "password2": "abd"})
        self.assertContains(r, "already taken")

    def test_crud_flow(self):
        self.client.login(username="alice", password="S3cure!pass99")
        self.client.post(reverse("mood"), {"mood": "happy", "reason": "Good day", "date": "2025-01-02"})
        self.assertEqual(Mood.objects.filter(user=self.a).count(), 1)
        self.client.post(reverse("journal_add"), {"title": "T", "date": "2025-01-02", "content": "hello", "mood": "calm", "tags": "a,b"})
        self.assertEqual(JournalEntry.objects.get().tag_list, ["a", "b"])
        self.client.post(reverse("routine_add"), {"title": "Run", "date": "2025-01-02", "category": "exercise", "priority": "high"})
        t = Task.objects.get()
        self.client.post(reverse("routine_toggle", args=[t.pk]))
        t.refresh_from_db(); self.assertTrue(t.completed)
        self.client.post(reverse("goals_add"), {"title": "Py", "start_date": "2025-01-01", "progress": 40, "status": "active"})
        g = Goal.objects.get()
        self.client.post(reverse("goals_progress", args=[g.pk]), {"progress": 100})
        g.refresh_from_db(); self.assertEqual(g.status, "completed")
        self.client.post(reverse("wellness"), {"date": "2025-01-02", "sleep_time": "23:00", "wake_time": "07:30", "quality": 4})
        self.assertEqual(float(SleepRecord.objects.get().duration), 8.5)
        self.client.post(reverse("wellness_water"), {"action": "add"})
        self.client.post(reverse("wellness_toggle", args=["read"]))
        self.client.post(reverse("calendar_add"), {"title": "Bday", "date": "2025-01-05", "category": "birthday", "reminder": "60"})
        self.client.post(reverse("routine_reminder_add"), {"title": "Pills", "date": "2099-01-05", "time": "08:00"})
        self.client.post(reverse("notes_add"), {"title": "N", "content": "c", "category": "ideas"})
        for name in ("dashboard", "mood", "journal", "calendar", "routine", "wellness", "goals", "notes"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_privacy_between_users(self):
        n = Note.objects.create(user=self.a, title="secret", content="x")
        j = JournalEntry.objects.create(user=self.a, title="diary", content="x", date=date.today())
        self.client.login(username="bob", password="S3cure!pass99")
        self.assertEqual(self.client.get(reverse("notes_edit", args=[n.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("notes_delete", args=[n.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("journal_delete", args=[j.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("notes")), "secret")
        self.assertNotContains(self.client.get(reverse("journal")), "diary")
        self.assertTrue(Note.objects.filter(pk=n.pk).exists())

    def test_settings_and_delete_account(self):
        self.client.login(username="alice", password="S3cure!pass99")
        self.client.post(reverse("settings"), {"action": "profile", "first_name": "Al", "username": "alice", "email": "new@x.com"})
        self.a.refresh_from_db(); self.assertEqual(self.a.email, "new@x.com")
        self.client.post(reverse("settings"), {"action": "password", "old_password": "S3cure!pass99",
                                               "new_password1": "N3wer!pass123", "new_password2": "N3wer!pass123"})
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)  # still logged in
        self.client.post(reverse("settings"), {"action": "delete", "password": "wrong"})
        self.assertTrue(User.objects.filter(username="alice").exists())
        self.client.post(reverse("settings"), {"action": "delete", "password": "N3wer!pass123"})
        self.assertFalse(User.objects.filter(username="alice").exists())

    def test_password_reset_page(self):
        self.assertEqual(self.client.get(reverse("forgot_password")).status_code, 200)
        r = self.client.post(reverse("forgot_password"), {"email": "a@x.com"})
        self.assertRedirects(r, reverse("password_reset_done"))
