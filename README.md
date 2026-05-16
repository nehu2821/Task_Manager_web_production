# TaskFlow — Team Task Manager

A full-stack web application for teams to manage projects and tasks with role-based access control. Built as part of the Ethara AI candidate nomination assignment.

**🌐 Live URL:** https://web-production-99dd0.up.railway.app
**📦 Repository:** https://github.com/HarnoorXtiet/Task-Manager
---

## Features

- **Authentication** — Signup and login with role selection (Admin / Member)
- **Project & team management** — Admins create projects and add members
- **Task management** — Create, assign, prioritize, and track tasks with due dates
- **Status tracking** — Tasks move through To Do → In Progress → Done
- **Role-based access control** — Admins manage; Members update only their assigned tasks
- **Dashboard** — Personalized view of projects, tasks, and overdue items
- **REST API** — Complete API with the same role-based permissions
- **Admin panel** — Django admin for power users

## Tech Stack

| Layer        | Technology                         |
|--------------|------------------------------------|
| Backend      | Django 5.1, Django REST Framework  |
| Database     | PostgreSQL (production), SQLite (local) |
| Frontend     | Django Templates + custom CSS      |
| Auth         | Django sessions + custom User model |
| Deployment   | Railway + Gunicorn + Whitenoise    |

## Database Schema

```
User (custom)
├── username, email, password
└── role: 'admin' | 'member'

Project
├── name, description
├── created_by → User (FK)
└── members ← Users (M2M)

Task
├── title, description
├── status: 'todo' | 'in_progress' | 'done'
├── priority: 'low' | 'medium' | 'high'
├── due_date
├── project → Project (FK)
├── assigned_to → User (FK, nullable)
└── created_by → User (FK)
```

## Role-Based Access Control

| Action               | Admin | Member |
|----------------------|-------|--------|
| Sign up / login      | ✅    | ✅    |
| View own projects    | ✅    | ✅ (only as member) |
| Create projects      | ✅    | ❌    |
| Edit / delete project | ✅ (if owner) | ❌ |
| Create tasks         | ✅    | ❌    |
| Edit / delete tasks  | ✅ (if project owner) | ❌ |
| Update task status   | ✅    | ✅ (only own tasks) |
| View all tasks in project | ✅ | ❌ (only own tasks) |

Permissions are enforced at the view layer (web) and permission_classes layer (API), not just in the UI.

## REST API Endpoints

All endpoints require authentication (session-based via `/api-auth/login/`).

| Method | Endpoint                      | Description                     | Permission     |
|--------|-------------------------------|----------------------------------|----------------|
| GET    | `/api/projects/`              | List user's projects             | Authenticated  |
| POST   | `/api/projects/`              | Create a project                 | Admin only     |
| GET    | `/api/projects/{id}/`         | Project detail with tasks        | Project member |
| PUT    | `/api/projects/{id}/`         | Update project                   | Admin only     |
| DELETE | `/api/projects/{id}/`         | Delete project                   | Admin only     |
| GET    | `/api/tasks/`                 | List visible tasks               | Authenticated  |
| POST   | `/api/tasks/`                 | Create a task                    | Admin only     |
| PATCH  | `/api/tasks/{id}/`            | Update status (members) or full (admins) | Authenticated |
| DELETE | `/api/tasks/{id}/`            | Delete task                      | Admin only     |
| GET    | `/api/users/`                 | List users (for assignment)      | Authenticated  |

### Example API request

```bash
# After logging in via /api-auth/login/
curl -X POST https://your-app.up.railway.app/api/projects/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf>" \
  --cookie "sessionid=<session>" \
  -d '{"name": "Q1 Roadmap", "description": "Goals for Q1"}'
```

## Local Setup

### Prerequisites
- Python 3.12+
- pip

### Steps

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd task-manager

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env
# (Edit .env if needed; defaults are fine for local SQLite)

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser (optional, for /admin)
python manage.py createsuperuser

# 7. Run the dev server
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Deployment (Railway)

1. Push the code to a GitHub repository.
2. Sign in to [Railway](https://railway.app) and create a new project from that repo.
3. Add a **PostgreSQL** plugin to the project. Railway automatically sets `DATABASE_URL`.
4. Add environment variables to the web service:
   - `SECRET_KEY` — long random string
   - `DEBUG` — `False`
5. Railway auto-detects Django and runs the `Procfile`. The app migrates and collects static files on every deploy.
6. Generate a public domain under **Settings → Networking → Generate Domain**.

## Project Structure

```
task-manager/
├── core/                    # Main app
│   ├── models.py           # User, Project, Task models
│   ├── views.py            # Web views with role checks
│   ├── api_views.py        # REST API viewsets
│   ├── serializers.py      # DRF serializers
│   ├── forms.py            # Django forms
│   ├── admin.py            # Django admin config
│   └── urls.py             # App URLs
├── taskmanager/            # Project settings
│   ├── settings.py
│   └── urls.py
├── templates/core/         # HTML templates
├── requirements.txt
├── Procfile                # Railway start command
├── runtime.txt             # Python version
└── manage.py
```

## How to Use

1. **Sign up** at `/signup/`. Pick **Admin** if you want to create projects, **Member** if you'll be assigned to them.
2. **As Admin:** Go to Dashboard → New Project → fill name and select team members → Save.
3. **As Admin:** Open the project → New Task → assign it to a member with a due date and priority.
4. **As Member:** Log in. Your dashboard shows only projects you're added to and tasks assigned to you. Open any task and update its status.
5. **API:** Visit `/api/` for the browsable DRF interface (login at `/api-auth/login/` first).

## Future Improvements

- Email notifications when tasks are assigned or due
- Real-time updates via WebSockets
- File attachments on tasks
- Task comments and activity log
- JWT auth for the API for true mobile/SPA support
- Drag-and-drop kanban board view

## Author

Built by Harnoor for the Ethara AI Software Engineer assessment.
