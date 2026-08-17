# System Architecture — Milestone 1

## 1. High-Level Architecture (current scope)

```
┌────────────────────┐        HTTPS/JSON        ┌─────────────────────────┐
│   React Frontend    │ ───────────────────────▶ │     FastAPI Backend      │
│  (Vite, port 5173)  │ ◀─────────────────────── │      (port 8000)          │
└────────────────────┘        JWT in header      └─────────────────────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │   SQLite DB        │
                                                   │  (injury_risk.db)  │
                                                   │  Users / Athletes   │
                                                   └──────────────────┘
```

This is the first slice of the full microservices architecture in the
project spec (User Management, Video Management, Pose Processing,
Biomechanical Analysis, Injury Risk Prediction, Anomaly Detection, Risk
Scoring, Recommendation, Analytics, Notification services sitting behind an
API Gateway). Milestone 1 implements the **User & Athlete Management**
service only; later milestones add the remaining services as separate
FastAPI routers (and eventually separate containers behind Docker Compose).

## 2. Request Flow (Auth)

1. User submits email/password to `POST /auth/login`.
2. Backend verifies the bcrypt password hash.
3. Backend issues a signed JWT containing the user's ID (`sub` claim).
4. Frontend stores the JWT in `localStorage` and attaches it as
   `Authorization: Bearer <token>` on every subsequent request.
5. Protected endpoints decode the JWT via a FastAPI dependency
   (`get_current_user`) and enforce role checks via `require_roles([...])`.

## 3. Database Schema

### `users`
| Column          | Type      | Notes                                  |
|-----------------|-----------|-----------------------------------------|
| id              | integer   | primary key                             |
| full_name       | string    |                                          |
| email           | string    | unique                                   |
| hashed_password | string    | bcrypt hash, never stored in plain text |
| role            | enum      | athlete / coach / physiotherapist / sports_scientist / admin |
| created_at      | datetime  |                                          |

### `athletes`
| Column          | Type      | Notes                                       |
|-----------------|-----------|-----------------------------------------------|
| id              | integer   | primary key                                   |
| athlete_code    | string    | unique human-readable ID (e.g. `ATH-001`)      |
| user_id         | integer   | FK → users.id (nullable; links athlete's own login) |
| sport_type      | string    |                                                |
| position        | string    | nullable                                       |
| age             | integer   |                                                |
| height_cm       | float     |                                                |
| weight_kg       | float     |                                                |
| injury_history  | text      | free text; structured injury records added in a later milestone |
| training_load   | string    | simple text for now (e.g. "High — 6 sessions/wk") |
| created_at      | datetime  |                                                |
| updated_at      | datetime  |                                                |

Both tables map directly onto the "Athlete Information" fields listed in the
project spec (Athlete ID, Sport Type, Position, Age, Height, Weight, Injury
History, Training Load) and the 5 user roles (Athlete, Coach,
Physiotherapist, Sports Scientist, Administrator).

## 4. Why SQLite for now?

The full spec calls for PostgreSQL + MongoDB + a vector DB + time-series DB
for the mature platform. For Milestone 1, SQLite keeps setup to zero
external dependencies so the auth + athlete-profile slice can be graded
without installing/configuring a database server. Swapping to PostgreSQL
later is a one-line change to `SQLALCHEMY_DATABASE_URL` in
`backend/app/database.py` since SQLAlchemy abstracts the engine.
