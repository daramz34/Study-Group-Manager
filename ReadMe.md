# StudyTogether

**Learn Together, Rank Together** 🎓

A social study app where students form study groups, set weekly goals, take AI-generated quizzes, and compete on group leaderboards through points and streaks.

---

## ✨ Features

- **👥 Study Groups** — create groups with invite codes, join via code, invite members by email, owner/admin role management (promote / demote / transfer ownership)
- **🎯 Weekly Goals** — members create study goals with topic content and deadlines per group
- **🤖 AI-Powered Quizzes** — quizzes are generated from goal content by **Gemini AI**:
  - 2 multiple-choice (4 options each)
  - 1 true/false
  - 2 short answer
- **📊 Instant Grading** — Gemini grades submissions and returns per-question feedback and correct answers
- **🏆 Leaderboards** — weekly (or all-time) rankings per group based on earned points
- **🔥 Streaks** — daily quiz streaks tracked per group, with longest-streak tracking
- **📚 Resources** — upload and share files (PDF, images, docs) via Cloudinary
- **🔐 Auth** — JWT-based registration/login (username + password), auto-login after signup
- **⚡ Rate limiting** on sensitive endpoints (slowapi)
- **📱 Fully responsive frontend** — pure HTML/CSS/JS (no framework), works on phone, tablet, and desktop


---
## 🎯 Problems & Solutions

### Who is it for?
Students — especially groups preparing for courses or exams together — who want structure,
accountability, and measurable progress instead of scattered, unmotivated studying.

| # | The Problem | How StudyTogether Solves It |
|---|-------------|-----------------------------|
| 1 | **Studying alone kills motivation** — easy to procrastinate when no one is watching. | Makes studying **social**: shared goals, visible peers, and a leaderboard turn revision into a team activity. |
| 2 | **Group study on chat apps is chaos** — notes get buried, no structure, no deadlines. | Each group gets **weekly goals with deadlines** and a **shared resource library** in one clean place. |
| 3 | **Practice questions barely exist** — writing good quizzes takes hours. | **Gemini AI generates a fresh 5-question quiz from the group's own study material** (MCQ, true/false, short answer) on demand. |
| 4 | **Manual marking is slow and inconsistent.** | Quizzes are **graded instantly by AI** with per-question scores and explanation-style feedback. |
| 5 | **Progress is invisible** — "am I actually improving?" | **Points, daily streaks, and per-group leaderboards** make progress objective and visible. |
| 6 | **Weak spots stay hidden** — generic past papers don't target your material. | Quizzes come from **your group's content**, and **question-level feedback** pinpoints exactly what to revise. |
| 7 | **Resources get lost in chats** — endless scrolling for that one PDF. | Files upload to Cloudinary and live in a **centralized per-group resource section**. |
| 8 | **Group coordination is admin hell** — who's in charge? how do people join? | **Invite codes, email invites, and owner/admin roles** (promote, demote, transfer ownership) handle it. |
| 9 | **Consistency dies after day one.** | **Streaks + points + rankings** reward daily practice — the same loop that makes games addictive, applied to studying. |

> **In one line:** StudyTogether turns unstructured solo cramming into a structured, social,
> gamified routine — AI writes and grades the questions, and the group keeps you honest.

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy 2.x |
| Database | PostgreSQL |
| AI | Google Gemini API (question generation + grading) |
| Auth | JWT (OAuth2 password flow) |
| File storage | Cloudinary |
| Rate limiting | slowapi |
| Scheduling | APScheduler (streak/leaderboard maintenance) |
| Frontend | HTML + Tailwind CSS (CDN) + vanilla JS |
| Serving | FastAPI serves the frontend as static files |

---

## 📁 Project Structure

```
Study_Group_Manager/
├── main.py                    # FastAPI app entry, CORS, static mount, lifespan
├── database.py                # SQLAlchemy engine/session
├── models.py                  # ORM models
├── schemas.py                 # Pydantic schemas
├── crud.py                    # Business logic (quizzes, points, streaks…)
├── core/
│   └── config.py              # Settings (env vars)
├── api/
│   └── v1/
│       ├── router.py          # API router aggregation
│       └── endpoint/
│           ├── auth.py        # register / login / me
│           ├── group.py       # groups, members, invites
│           ├── goal.py        # goals
│           ├── quiz.py        # start-quiz / submit
│           ├── leaderboard.py # leaderboard
│           ├── resource.py    # resource uploads
│           └── dashboard.py   # dashboard stats
├── services/
│   ├── gemini.py              # Gemini question generation + grading
│   ├── cloudinary_service.py  # file upload
│   ├── email_service.py       # invite emails
│   └── scheduler.py           # background jobs
└── frontend/                  # served at "/"
    ├── index.html             # Landing page
    ├── auth.html              # Login / Register
    ├── dashboard.html         # Stats + groups
    ├── groups.html            # Group list
    ├── group.html             # Group detail (goals, members)
    ├── quiz.html              # Take quiz + results review
    ├── leaderboard.html       # Rankings
    ├── resources.html         # Shared resources
    ├── css/custom.css
    └── js/                    # api.js, app.js, auth.js, etc.
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- PostgreSQL
- Gemini API key
- Cloudinary account (optional, for resources)
- SMTP/email credentials (optional, for invites)

### 2. Environment variables (`.env`)

```env
# App
SECRET_KEY=your-jwt-secret
APP_NAME=StudyTogether
VERSION=1.0.0

# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/studygroup_db

# Gemini AI
GEMINI_API_KEY=your-gemini-key

# Cloudinary (resources)
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=your-key
CLOUDINARY_API_SECRET=your-secret

# Email (group invites)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=your-password
```

### 3. Install & run

```bash
# create venv and install
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt

# start the server
uvicorn main:app --reload
```

Open:
- **App:** http://127.0.0.1:8000/
- **API docs (Swagger):** http://127.0.0.1:8000/docs

> Tables are created automatically on startup (`Base.metadata.create_all`).

---

## 🔌 API Overview

All routes are prefixed with `/api/v1`.

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account (username, email, password) |
| POST | `/auth/login` | Login (OAuth2 form: `username` + `password`) → JWT |
| GET | `/users/me` | Current user profile |

### Groups & Members
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/groups/` | List my groups |
| POST | `/groups/` | Create group (returns invite code) |
| POST | `/groups/join` | Join with `invite_code` |
| POST | `/groups/{id}/invite` | Owner/admin invite by email |
| … | `/members/…` | Promote / demote / transfer ownership |

### Goals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/goals/group/{group_id}` | List a group's goals |
| POST | `/goals/group/{group_id}` | Create a goal (title, topic_content, deadline…) |

### Quiz (Gemini)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/quiz/goals/{goal_id}/start-quiz` | Generate & start a 5-question quiz (5/day limit) |
| POST | `/quiz/{quiz_id}/submit` | Submit answers → graded score + feedback + points |

> One quiz per goal per day — retaking returns **400 "Quiz already taken"**.

### Leaderboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/leaderboard/{group_id}?week=N` | Ranked members; `week=0` = all time |

### Resources
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/resources/groups/{group_id}` | List shared resources |
| POST | `/resources/groups/{group_id}` | Upload (multipart) → Cloudinary URL |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/users/me` | Points, streak, quizzes, goals stats |

---

## 🎮 How Scoring Works

- Each quiz is graded out of **10** (5 questions × 2 pts).
- Awarded points: `max(3, round(percentage × 20))` — up to **20 points** per quiz.
- Scoring **≥ 50%** marks the goal as **completed**.
- Submitting a quiz **increments your daily streak** (tracked per group).
- Quiz questions/answers/feedback are stored as JSON; graded quizzes are one-time only.

---

## 🌐 Frontend

Plain HTML + Tailwind + vanilla JS, served by FastAPI at `/`.

| Page | Purpose |
|------|---------|
| `index.html` | Landing / hero |
| `auth.html` | Login & register (auto-login after signup) |
| `dashboard.html` | Stats, pending goals, deadlines |
| `groups.html` | Browse / create / join groups |
| `group.html` | Group goals + quick links |
| `quiz.html` | Take quiz → results review (score + correct answers) |
| `leaderboard.html` | Weekly / all-time rankings |
| `resources.html` | View & upload shared files |

API base URL + token handling lives in `frontend/js/api.js`.

---

## ✅ Roadmap / Nice-to-Haves
- Quiz history endpoint so users can revisit past graded quizzes
- Retake (best-score) support
- Password reset flow
- Production CORS allow-list & HTTPS

---


