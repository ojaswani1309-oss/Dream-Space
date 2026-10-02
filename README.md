# Dream Space ✨

A private, dreamy personal wellness space: mood tracker, journal, mood-based music, calendar, routine planner,
reminders, wellness (water, sleep, daily activities), goals and private notes.
Django + Django Templates + MySQL. Every record belongs to a user and every query is filtered by the logged-in user.

## 1. Requirements
- Python 3.10+
- MySQL 8.0+ (or MariaDB 10.5+)

## 2. Python environment
```bash
cd dream_space
python -m venv venv
# Windows:  venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
```
Packages: `Django`, `PyMySQL` (pure-Python MySQL driver, no compiler needed) and `cryptography` (MySQL 8 auth).
If you prefer `mysqlclient`, install it instead and it is used automatically.

## 3. Create the MySQL database
```sql
CREATE DATABASE dream_space CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- optional dedicated user:
CREATE USER 'dream'@'localhost' IDENTIFIED BY 'a-strong-password';
GRANT ALL PRIVILEGES ON dream_space.* TO 'dream'@'localhost';
FLUSH PRIVILEGES;
```
(`utf8mb4` is required so emojis are stored correctly.)

## 4. Configure
Copy `.env.example` to `.env` and fill in your values (never commit `.env`):
```
DB_NAME=dream_space
DB_USER=dream
DB_PASSWORD=a-strong-password
DB_HOST=127.0.0.1
DB_PORT=3306
DJANGO_SECRET_KEY=<long random string>
```
These are read in `dream_space/settings.py`. Set `TIME_ZONE` there too (e.g. `Asia/Kolkata`) so "today" matches your day.

## 5. Migrate and run
```bash
python manage.py migrate
python manage.py runserver
```
Open http://127.0.0.1:8000 → sign up → your dashboard.
Optional: `python manage.py createsuperuser` for the `/admin/` site.

## Password reset
By default, reset emails are printed in the terminal running the server (copy the link into your browser).
For real email set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` and the `EMAIL_*` values in `.env`.

## Tests
`python manage.py test` (set `DB_ENGINE=sqlite` to run without MySQL). They cover login, signup, CRUD flows,
settings, account deletion and that one user can never read or change another user's data.

## Notes
- Music: no audio is stored. Songs link out to YouTube/Spotify searches.
- Browser reminder notifications: enable in Settings → Preferences, allow notifications, keep a Dream Space tab open.
- Production: set `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, serve over HTTPS and run `collectstatic`.

## Structure
```
dream_space/  settings.py urls.py wsgi.py asgi.py
core/         models.py views.py forms.py urls.py admin.py backends.py context.py music_data.py tests.py migrations/
templates/    base.html + one template per page
static/       css/style.css  js/app.js  images/
```
