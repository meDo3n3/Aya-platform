# HifzTracker (Starter)

A simple Django + MySQL starter for a Quran memorization tracker (Student/Teacher/Admin).

## Quick Start

1. **Python & MySQL**
   - Python 3.11+ recommended
   - MySQL 8+ and create a database:
     ```sql
     CREATE DATABASE hifztracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     ```

2. **Set up environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
   Fill `.env` with your values.

3. **Migrate & create admin**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

4. **Login**
   - Visit `/admin` to add Halaqat and Students, or use the built-in forms at `/tracker/...`
   - Default auth routes:
     - `/accounts/login/`
     - `/accounts/logout/`

## Roles
- Use Django admin to create users and a matching `Profile` with role = student/teacher/admin.
- Students need a `Student` linked to their `User` (see admin).

## Notifications
- Configure Twilio in `.env`. Add your sending logic inside `apps/tracker/notifications.py` (stub).

## Notes
- This is a minimal starter. Add permissions, validations, and tests per your needs.
