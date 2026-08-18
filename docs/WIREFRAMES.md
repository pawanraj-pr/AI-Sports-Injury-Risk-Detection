# UI Wireframes / Workflow Planning — Milestone 1

These describe the implemented screens (matching what you'll see running the
frontend). Rough layout is described in text/ASCII since hand-drawn wireframe
images aren't needed once the real screens exist.

## 1. Login
```
 ┌─────────────────────────────┐
 │  Login                       │
 │  Email    [______________]   │
 │  Password [______________]   │
 │        [ Login ]              │
 │  No account? Register here    │
 └─────────────────────────────┘
```

## 2. Register
```
 ┌─────────────────────────────┐
 │  Create Account               │
 │  Full Name [______________]   │
 │  Email     [______________]   │
 │  Password  [______________]   │
 │  Role      [ dropdown: athlete / coach /
 │              physiotherapist / sports_scientist / admin ] │
 │        [ Register ]            │
 └─────────────────────────────┘
```

## 3. Home / Landing
```
 ┌───────────────────────────────────────────┐
 │  Sports Injury Risk Detection Platform       │
 │  <short description>                          │
 │  Welcome back, <name> (<role>)                │
 │  [ Go to Athlete Profiles ]                    │
 └───────────────────────────────────────────┘
```

## 4. Athlete List (Athlete Dashboard / Coach Dashboard shared view)
```
 ┌───────────────────────────────────────────┐
 │  Athlete Profiles          [+ New Athlete]  │  ← button hidden for "athlete" role
 │ ─────────────────────────────────────────── │
 │ Code   Sport   Pos  Age  Ht  Wt  Load  Actions│
 │ ATH-1  Soccer  FWD  22  180 75  High  View|Edit|Delete
 │ ATH-2  Basketball G  24  190 88  Med   View|Edit|Delete
 └───────────────────────────────────────────┘
```
Athletes logged in only ever see their own row (enforced server-side, not
just hidden in the UI).

## 5. Athlete Create / Edit Form
```
 ┌─────────────────────────────┐
 │  New Athlete                   │
 │  Athlete Code   [______]        │
 │  Sport Type     [______]        │
 │  Position       [______]        │
 │  Age            [______]        │
 │  Height (cm)    [______]        │
 │  Weight (kg)    [______]        │
 │  Injury History [textarea]      │
 │  Training Load  [______]        │
 │       [ Save ]                   │
 └─────────────────────────────┘
```

## 6. Athlete Detail (read-only view)
```
 ┌─────────────────────────────┐
 │  ATH-001                       │
 │  Sport Type: Soccer            │
 │  Position: Forward              │
 │  Age: 22                        │
 │  Height: 180 cm                 │
 │  Weight: 75 kg                  │
 │  Training Load: High             │
 │  Injury History: ACL tear (2023) │
 │  ← Back to list                  │
 └─────────────────────────────┘
```

## Navigation flow

```
Login/Register ──▶ Home ──▶ Athlete List ──▶ Athlete Detail
                                   │
                                   ├──▶ New Athlete Form
                                   └──▶ Edit Athlete Form
```

Coach/Physio/Sports Scientist/Admin dashboards described in the full spec
(team risk overview, rehab tracking, biomechanical analytics, etc.) will be
built out on top of this same navigation shell in Milestones 2–4, once
video/pose/risk data exists to display.
