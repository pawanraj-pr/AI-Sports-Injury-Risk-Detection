# Sports Injury Risk Detection from Video

## 1. Project Objective

An AI-powered platform that analyzes athlete movement videos to identify
biomechanical issues, detect abnormal movement patterns, assess injury risk
factors, and predict potential injuries before they occur — using computer
vision, pose estimation, biomechanics analysis, and predictive analytics.

This repository covers **Milestones 1 through 4** (all 8 weeks of the
original project plan):

**Milestone 1 — Project Initialization, Design Process & Core Setup**
- [x] Project objectives & injury detection workflow definition
- [x] System architecture & database schema (see `docs/ARCHITECTURE.md`)
- [x] UI wireframes / workflow planning (see `docs/WIREFRAMES.md`)
- [x] Backend + frontend environment setup
- [x] Authentication (JWT) + role-based access control (4 roles)
- [x] Athlete profile management (create / view / edit / delete)
- [x] Recommended biomechanics datasets documented (see `docs/DATASETS.md`)

**Milestone 2 — Pose Estimation & Biomechanical Analysis**
- [x] Video upload & processing engine (`/videos/upload`)
- [x] Pose estimation engine using MediaPipe (`backend/app/pose_analysis.py`)
- [x] Biomechanical analysis: knee angles, knee valgus, hip stability, trunk
      lean, landing mechanics, stride length, joint alignment, balance,
      movement symmetry
- [x] Movement quality scoring (0–100) + risk category (Low/Moderate/High/Critical)
- [x] Frontend: drag-and-drop upload, live processing status, animated score
      gauge, bar-chart metric breakdown, raw joint measurement table

**Milestone 3 — Injury Prediction, Anomaly Detection & Recommendations**
- [x] Injury Risk Prediction Engine (weighted model: 35/20/20/15/10)
- [x] Injury category breakdown (ACL, Hamstring, Ankle, Shoulder, Lower
      Back, Overuse)
- [x] Movement Anomaly Detection Engine (per-athlete baseline comparison)
- [x] Corrective Recommendation Engine (rules-based, categorized)
- [x] Athlete Intelligence Dashboard with animated gauge, charts, PDF export
- [x] Athlete self-service: create/edit own profile, own videos only,
      combined multi-video report, PDF export

**Milestone 4 — Admin Dashboard, Team Overview, Deployment & Testing**
- [x] Sports Scientist role removed platform-wide
- [x] Login tracking + admin user management (activate/deactivate)
- [x] Admin Dashboard with pie charts (users by role, logins by role) +
      platform stats
- [x] Team Overview dashboard (Coach/Physiotherapist/Admin) — team risk
      overview + injury risk monitoring
- [x] Excel export alongside existing PDF export
- [x] Automated test suite (pytest)
- [x] Docker deployment (backend + frontend + docker-compose)

## 2. Repository Structure

```
injury-risk-platform/
├── backend/                 FastAPI service
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── requirements-dev.txt  Adds pytest + httpx for running tests
│   ├── tests/                pytest suite (auth/RBAC, self-service, risk engine, admin)
│   └── app/
│       ├── main.py           App entrypoint
│       ├── models.py         SQLAlchemy models (User, Athlete, Video, BiomechanicsReport)
│       ├── schemas.py        Pydantic request/response schemas
│       ├── auth.py           JWT + password hashing + role dependency
│       ├── database.py       SQLite engine/session
│       ├── pose_analysis.py  MediaPipe pose estimation + biomechanical metric engine
│       ├── risk_engine.py    Injury risk prediction, anomaly detection, recommendations
│       ├── report_pdf.py     PDF report generation (video / combined / risk assessment)
│       ├── report_excel.py   Excel (.xlsx) combined report export
│       ├── uploads/           Uploaded video files land here
│       └── routers/
│           ├── auth.py       /auth/register, /auth/login, /auth/me
│           ├── athletes.py   /athletes CRUD, self-service, reports, risk assessment, team overview
│           ├── videos.py     /videos upload, process, list, detail, delete, PDF report
│           └── admin.py      /admin dashboard stats + user management (admin-only)
├── frontend/                 React + Vite single-page app
│   ├── Dockerfile             Multi-stage build, served via nginx
│   ├── nginx.conf
│   └── src/
│       ├── pages/            Login, Register, Home, AthleteList/Form/Detail, MyProfile,
│       │                     RiskAssessment, TeamOverview, AdminDashboard, VideoUpload/List/Detail
│       ├── context/           AuthContext (stores JWT + role)
│       ├── components/        Navbar, ProtectedRoute, Backdrop, ScoreGauge, PoseLoader, Illustrations
│       └── api.js             fetch wrapper for the backend API
├── docker-compose.yml         Runs backend + frontend together
└── docs/
    ├── ARCHITECTURE.md       System architecture + DB schema
    ├── WIREFRAMES.md         Screen-by-screen wireframe descriptions
    └── DATASETS.md           Recommended datasets for later milestones
```

## 3. How to Run It

> **If you're updating from an earlier version of this project:** the
> `users` table gained `is_active`/`login_count`/`last_login_at` columns,
> the `sports_scientist` role was removed entirely, and the `athletes`
> table gained `injury_severity`/`training_load_level` (Milestone 3). If
> you already have a running `injury_risk.db`, delete it so the schema
> regenerates cleanly:
> ```powershell
> cd backend
> del injury_risk.db
> ```
> (It's just your local dev/test data — a fresh empty database is created
> automatically the next time you start the server. You'll need to
> re-register accounts and re-create athlete profiles afterward — and use
> a role other than Sports Scientist, since it no longer exists.)
> Install the new Milestone 4 backend dependency (openpyxl, for Excel export):
> ```powershell
> python -m pip install -r requirements.txt
> ```

### Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API runs at **http://127.0.0.1:8000**
- Interactive API docs (Swagger UI) at **http://127.0.0.1:8000/docs**
- A `injury_risk.db` SQLite file is created automatically on first run — no
  external database setup needed for this milestone.

### Frontend (React + Vite)

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

- App runs at **http://127.0.0.1:5173**

### Try it end-to-end

1. Go to `/register`, create an account with role `coach` (or `admin`,
   `physiotherapist`, `sports_scientist`).
2. Log in.
3. Go to **Athletes** → **+ New Athlete** and create an athlete profile.
4. Register a second account with role `athlete` and log in — notice it
   can only view athlete profiles, not create/edit/delete them (role-based
   access control in action).

## 4. Roles & Permissions (implemented)

> **Note:** the Sports Scientist role from the original spec has been
> removed at the requester's direction — the platform now has 4 roles:
> Athlete, Coach, Physiotherapist, Admin.

| Role              | View athletes | Create/Edit athletes | Delete athletes | Team Overview | Admin Dashboard |
|-------------------|:---:|:---:|:---:|:---:|:---:|
| athlete           | own profile only | ✗ | ✗ | ✗ | ✗ |
| coach             | all | ✓ | ✗ | ✓ | ✗ |
| physiotherapist   | all | ✓ | ✗ | ✓ | ✗ |
| admin             | all | ✓ | ✓ | ✓ | ✓ |

## 5. Tech Stack Used (Milestone 1)

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite (swap for PostgreSQL later), python-jose (JWT), passlib (bcrypt)
- **Frontend:** React 18, Vite, React Router
- **Auth:** JWT bearer tokens, role-based access control (RBAC)

Later milestones will add: pose estimation (MediaPipe/OpenPose), OpenCV video
processing, biomechanical analysis, ML-based risk scoring, and Docker
deployment — as outlined in the full project spec.

## 6. Try Milestone 2 end-to-end

1. Log in as a `coach` (or physio/sports_scientist/admin).
2. Go to **Athletes**, open an athlete profile → **Upload Movement Video**.
3. Choose an activity type (running, jumping, landing, etc.), pick a short
   clip of a person moving (a few seconds is enough — the engine samples
   every 3rd frame), and upload.
4. You're redirected to the video detail page, which polls automatically
   while MediaPipe processes the clip in the background.
5. Once complete, you'll see:
   - An animated **movement quality score** gauge (0–100) with a risk
     category (Low/Moderate/High/Critical)
   - A **bar chart** breaking down hip stability, landing mechanics, joint
     alignment, balance, symmetry, and knee valgus
   - A table of raw joint angle measurements

**Tip:** a clear, well-lit video with the full body visible (e.g. someone
jogging or squatting on their phone camera) gives MediaPipe the best chance
of detecting pose landmarks. Videos with no visible person will fail
processing with an explanatory error message rather than silently returning
nothing.

## 7. Tech Stack Used (Milestone 1 + 2)

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite, python-jose (JWT), passlib (bcrypt)
- **Pose Estimation / Biomechanics:** MediaPipe Pose, OpenCV (opencv-python-headless), NumPy
- **Frontend:** React 18, Vite, React Router, Recharts (charts), lucide-react (icons)
- **Auth:** JWT bearer tokens, role-based access control (RBAC)

## 8. Design System

The frontend uses a custom "biomechanics lab readout" visual identity rather
than a generic dashboard template:

- **Palette:** pale sage-mist background, near-black ink text, electric
  indigo primary accent, signal orange for emphasis. Risk badges keep a
  semantic green → amber → orange → red scale (Low → Critical).
- **Type:** Space Grotesk for headlines, IBM Plex Sans for body text, IBM
  Plex Mono for every number/score/angle — so data reads like an instrument
  readout.
- **Signature element:** an animated waveform trace across the homepage
  hero — modeled on the actual joint-angle time-series data the pose
  estimation engine produces — that draws itself in once on page load.
- Motion respects `prefers-reduced-motion`; layout is responsive down to
  mobile widths.

All colors/fonts are defined as CSS custom properties at the top of
`frontend/src/styles.css` (`:root { --bg, --accent, --font-display, ... }`)
so the whole look can be retuned from one place.

## 9. Athlete Self-Service, Combined Reports & PDF Export

Athlete-role accounts now manage their own data end-to-end, without needing
a coach/admin to set anything up on their behalf:

- **First login as an athlete** → the nav shows **"My Profile"** instead of
  "Athletes." If no profile exists yet, a creation form appears
  (`GET/POST /athletes/me`) — the athlete fills in their own Athlete Code,
  Sport Type, Position, Age, Height, Weight, Injury History, and Training
  Load. This profile is automatically linked to their login (`user_id`),
  and — as before — an athlete can only ever see or upload videos for
  **their own** profile, never anyone else's.
- **Multiple videos, one combined report** — every video an athlete
  uploads gets its own individual biomechanics report (as in Milestone 2),
  but "My Profile" now also shows a **Combined Report** panel that averages
  every completed video's metrics together (`GET
  /athletes/{id}/reports/summary`), with a per-video comparison table.
- **PDF export** — both the individual video report (on the video detail
  page) and the combined multi-video report (on "My Profile") have a
  **Download PDF Report** button, generated server-side with `fpdf2`
  (`GET /videos/{id}/report/pdf` and `GET
  /athletes/{id}/reports/summary/pdf`).

Coaches/physios/sports scientists/admins are unaffected — they still use
the existing **Athletes** list to create/edit profiles on behalf of
athletes who don't self-register, and can view/download the same reports
for any athlete they manage.

## 10. Milestone 3 — Injury Prediction, Anomaly Detection & Recommendations

Builds directly on Milestone 2's per-video biomechanics reports to produce
an **athlete-level** injury risk assessment.

### Injury Risk Prediction Engine (`backend/app/risk_engine.py`)

Implements the exact weighted model from the project spec:

```
Injury Risk Score =
    Biomechanical Deviations   (35%)  — avg. inverse of movement quality across all videos
  + Historical Injury Factors  (20%)  — from the athlete's Injury Severity field
  + Movement Asymmetry         (20%)  — avg. inverse of movement symmetry across all videos
  + Training Load Indicators   (15%)  — from the athlete's Training Load Level field
  + Fatigue Indicators         (10%)  — recent video quality vs. the athlete's own baseline
```

Risk Categories: **Low** (<30) / **Moderate** (<50) / **High** (<70) / **Critical** (≥70).

Two new structured fields drive this (added to Athlete Profile Management):
**Injury Severity** (none/mild/moderate/severe) and **Training Load Level**
(low/moderate/high/very high) — separate from the existing free-text
Injury History and Training Load notes fields, which stay for descriptive
context.

### Injury Category Breakdown

Per-category elevated-risk indicators (not clinical probabilities) for the
6 categories in the spec — ACL, Hamstring, Ankle Sprain, Shoulder, Lower
Back, Overuse — each built from the biomechanical metrics most associated
with that injury type (e.g. ACL risk combines knee valgus + landing
mechanics; shoulder risk only activates when throwing/cricket-activity
videos exist).

### Movement Anomaly Detection Engine

Flags individual videos that deviate sharply from the athlete's **own**
historical baseline — a notable drop in movement quality or spike in knee
valgus versus their other videos — surfacing possible technique breakdown
or fatigue rather than just reporting a static score.

### Corrective Recommendation Engine

A rules engine that reads the computed risk factors and returns concrete,
categorized suggestions (Exercise / Mobility / Strengthening / Recovery /
Training Modification) — e.g. glute/hip strengthening when ACL risk is
elevated, Nordic curls for hamstring asymmetry, balance drills for ankle
risk, load management when overuse risk or fatigue is high.

### Athlete Intelligence Dashboard

New page at `/athletes/{id}/risk-assessment` (linked from both the staff
Athlete Detail page and the athlete's own "My Profile"): animated overall
risk gauge, weighted-component bar chart, injury-category bar chart with
notes, anomaly alert cards, recommendation cards, and a **Download PDF
Report** button (`GET /athletes/{id}/risk-assessment/pdf`).

**Honest caveat, stated on-page and in the PDF itself:** this is a
non-clinical, heuristic assessment built from simplified 2D pose-estimation
metrics — not a medical diagnosis, and not a substitute for evaluation by a
qualified physiotherapist or sports medicine physician.

## 11. Milestone 4 — Admin Dashboard, Team Overview, Deployment & Testing

### Role change: Sports Scientist removed

The Sports Scientist role from the original spec has been removed
platform-wide (enum, permission lists, registration form). The platform
now has 4 roles: **Athlete, Coach, Physiotherapist, Admin**.

> If you have an existing `injury_risk.db` with `sports_scientist` accounts
> in it, delete the DB file (see the note at the top of "How to Run It")
> before starting the backend — the old enum value will no longer load.

### Login tracking & user management

Every login now increments a `login_count` and updates `last_login_at` on
the `users` table. Accounts can be deactivated (`is_active = false`) by an
admin, which immediately blocks further logins with a clear error message.

### Admin Dashboard (`/admin`, admin-only)

New page with:
- **Stat cards**: total users (active/inactive), athlete profiles, videos
  uploaded/analyzed, high & critical risk report count
- **"Registered Users by Role" pie chart** and **"Logins by Role" pie
  chart** — directly answers "how many people are using / logging into the
  platform," broken down by role
- **User management table**: every account with role, status, login count,
  last login, join date, and a one-click **Activate/Deactivate** toggle
- **Recently registered** accounts list

Backed by `GET /admin/dashboard`, `GET /admin/users`, and
`PUT /admin/users/{id}/toggle-active` — all admin-only.

### Team Overview (`/team`, Coach/Physiotherapist/Admin)

A shared dashboard satisfying both the spec's "Coach Dashboard — Team risk
overview" and "Physiotherapist Dashboard — Injury risk monitoring": every
athlete in one table (sport, injury severity, training load, video count,
latest movement quality score, latest risk category), with athletes
needing attention (moderate/severe injury history, or High/Critical latest
risk) surfaced at the top as alert cards. Backed by
`GET /athletes/team/overview`.

### Reports & Export System: Excel added

Alongside the existing PDF export, athletes/staff can now download a
**combined report as an Excel workbook** (`GET
/athletes/{id}/reports/summary/excel`, via `openpyxl`) — a Summary sheet
with averaged metrics plus a Videos sheet with the full per-video
breakdown. Button lives next to "Download PDF" on the athlete's profile.

### Automated tests

`backend/tests/` — a pytest suite covering registration/login/RBAC, the
self-service athlete profile flow, the injury risk engine, and the new
admin endpoints, run against an isolated temporary SQLite database (never
touches your real `injury_risk.db`). Install and run:
```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest
```

### Docker deployment

- `backend/Dockerfile` — Python 3.12-slim + the OS libraries `opencv`/
  `mediapipe` need at runtime
- `frontend/Dockerfile` — multi-stage: builds the Vite app, serves the
  static files with nginx (`frontend/nginx.conf` handles React Router's
  client-side routing fallback)
- `docker-compose.yml` at the repo root — runs both together

```powershell
docker compose up --build
```
Backend on `http://localhost:8000`, frontend on `http://localhost:5173`.

**Known limitation, stated plainly:** the SQLite database and uploaded
videos live inside the backend container's writable layer, not a
persistent volume mount (mounting a volume at `/app` would hide the
application code baked into the image). Data survives container restarts
but not `docker compose down -v` or image rebuilds. Swapping to PostgreSQL
(already noted as the intended production path in `database.py`) would be
the right fix before a real deployment — Docker here demonstrates the
containerization/deployment capability the spec asks for, not a
production-hardened persistence setup.

## 12. What's Not Included

A few Milestone 4 spec items were judged lower-value for a project at this
stage and left out rather than half-implemented:
- **Notification & Alert System** (push/email alerts) — would need real
  email/push infrastructure; the same information (high-risk athletes,
  anomalies) is instead surfaced directly in the Team Overview and Risk
  Assessment dashboards, which is more useful for a locally-run demo.
- **Live cloud deployment (AWS/Azure)** — Docker files are provided and
  ready for that step, but actually provisioning cloud infrastructure is
  outside what can be delivered/verified in this environment.

## 13. Bug Fixes in This Update

### Injury Risk Assessment PDF download was failing ("Failed to fetch")

**Root cause:** fpdf2's core fonts (Helvetica) only support Latin-1
encoding. Several strings feeding into that specific PDF — the fallback
"no risk factors detected" recommendation text and the anomaly-detection
description — contained an em dash (—, U+2014), which is outside Latin-1.
fpdf2 raises `FPDFUnicodeEncodingException` when it hits an unsupported
character, crashing the request before a response could be sent. Since the
fallback recommendation fires on almost every low-risk assessment, this
was hit consistently, while the video-report and combined-report PDFs
(which never contained that character) worked fine.

**Fix:** replaced the em dashes with plain hyphens at the source
(`risk_engine.py`), and — more importantly — added a `_safe()` sanitizer
in `report_pdf.py` that every piece of dynamic PDF text now passes
through, so any future non-Latin1 character (in user-entered athlete/sport
names, video filenames, etc.) gets safely substituted instead of crashing
the whole report.

### Admin Dashboard login/join times were wrong

**Root cause:** the backend stores timestamps as naive UTC
(`datetime.utcnow()`), so the JSON sent to the frontend has no timezone
marker. Browsers interpret a timezone-less timestamp as **local time, not
UTC** — so the displayed time was off by the viewer's UTC offset (5.5
hours for IST viewers), not just unlabeled.

**Fix:** added `frontend/src/utils.js` with a `formatIST()` helper that
explicitly treats the backend's timestamp as UTC, then formats it in
Asia/Kolkata (IST) with an "IST" label — used for both "Last Login" and
"Joined" columns on the Admin Dashboard.

## 14. Second Round: Injury Risk Assessment PDF Was Still Failing

After the Section 13 fix, the download could still fail — traced to a
second, separate bug plus a frontend issue that made any failure look
worse than it was.

### Frontend bug: a failed download blanked the entire page

`RiskAssessment.jsx` was using the same `error` state for both the
initial page-load fetch and the "Download PDF" button. If the download
failed for any reason, the whole page — gauge, charts, recommendations,
everything — got replaced by a single line of raw error text (including
the literal browser string `"Failed to fetch"` if that's what occurred).
**Fixed:** the download now has its own `downloadError` state, shown
inline next to the button. If it's genuinely a `"Failed to fetch"`
network-level error, the message now explicitly says to confirm the
backend is running at `http://127.0.0.1:8000` — turning a cryptic browser
error into an actionable one.

### Backend hardening: PDF/Excel generation no longer produces unhandled crashes

Every PDF/Excel-generating endpoint (`/videos/{id}/report/pdf`,
`/athletes/{id}/reports/summary/pdf`, `/athletes/{id}/reports/summary/excel`,
`/athletes/{id}/risk-assessment/pdf`) now wraps its file-building step in a
try/except that returns a clean `500` with a specific message instead of
letting any unexpected error propagate unhandled.

### Backend hardening: Content-Disposition filenames are now sanitized

Added `backend/app/http_utils.py` with a `safe_filename()` helper, applied
everywhere a download filename is built from `athlete.athlete_code`. HTTP
header values must be plain ASCII with no quotes/control characters —
without this, an athlete code containing anything unusual could produce a
malformed header that some ASGI server configurations reject by resetting
the connection outright (which the browser reports as a generic network
failure rather than a normal HTTP error).

### Verification performed

The actual `build_risk_assessment_pdf()` function was run — not
re-inspected, actually executed — against a stub that replicates fpdf2's
real crash behavior (raises on any non-Latin1 character, exactly like the
real library does), across four scenarios: a low-risk assessment hitting
only the fallback recommendation (the exact case that was broken), a
high-risk assessment with anomalies and every recommendation category
firing, a video filename containing emoji/accented characters, and a
sparse/zero-video edge case. All four now pass.

**If the download still fails after this update:** the inline error
message will now show the real reason (not just "Failed to fetch")
unless it's a genuine connectivity problem — in which case, confirm the
backend terminal is running without errors and reachable at
`http://127.0.0.1:8000/docs` in a browser tab.

## 15. Risk Assessment PDF Now Matches the Web Page Layout

The downloaded PDF previously only listed scores as plain text rows. It
now visually mirrors the Risk Assessment web page:

- **Weighted Risk Components** — an actual horizontal bar chart (drawn
  natively with fpdf2's own drawing primitives, no extra dependency),
  color-coded by risk category exactly like the site
- **Injury Category Breakdown** — the same bar-chart treatment
- **Category Notes** — each injury category's score, risk category, and
  explanatory note (previously the note text wasn't in the PDF at all)
- **Corrective Recommendations** — each recommendation's category now
  appears as a bold label above its text, instead of run together in one line

Re-verified with an extended test harness covering zero scores, a
maximum (100) score, a missing/`None` score, and a video filename with
emoji + accented characters — all render without error.
