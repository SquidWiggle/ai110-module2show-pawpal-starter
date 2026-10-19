# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

An example usage of the CLI app is in main.py.
1. Define pets Tama (cat) and Pochi (dog).
2. Create tasks for Tama (cat) and Pochi (dog). Tama (cat) requires feedings. Pochi (dog) requires both feedings and walks.
3. Create an Owner with default work & sleep time blocks blacked out so the scheduler understands the available times for pet tasks.
4. Schedule their 3 tasks.
5. Get all the scheduled task and print them out.
Run main.py
```bash
python3 main.py
```
```
Scheduled Tasks:
Time              Task            Pet        Duration   Priority
------------------------------------------------------------
2024-06-01 08:00  Feed Tama       Tama       15m        HIGH
2024-06-01 08:30  Feed Pochi      Pochi      15m        HIGH
2024-06-01 10:00  Walk Pochi      Pochi      30m        MEDIUM
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sameen/CodePath/ai110-module2show-pawpal-starter
plugins: cov-7.1.0, anyio-4.15.1
collecting ... collected 15 items

test_pawpal.py ...............                                           [100%]

================================ tests coverage ================================
______________ coverage: platform darwin, python 3.13.15-final-0 _______________

Name               Stmts   Miss  Cover
--------------------------------------
pawpal_system.py     278     56    80%
test_pawpal.py       162      0   100%
--------------------------------------
TOTAL                440     56    87%
============================== 15 passed in 0.40s ===============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.organize_tasks()` | Sorts tasks primarily chronologically by `due_date`, then by priority (`HIGH: 0`, `MEDIUM: 1`, `LOW: 2`). |
| Filtering | `Scheduler.see_todays_tasks()`, `Owner.get_all_tasks()` | `see_todays_tasks()` filters tasks matching a specific date (`target_date`), excludes completed tasks during conflict/slot analysis, and delegates multi-pet task aggregation to `Owner.get_all_tasks()`. |
| Conflict handling | `TimeSlot.overlaps()`, `Scheduler.alert_conflict()`, `Scheduler.suggest_time_slot()` | `alert_conflict()` identifies pairwise overlapping uncompleted tasks and collisions against `Owner.blocked_times`. `suggest_time_slot()` finds the earliest open window in available times skipping task and block conflicts. |
| Recurring tasks | `TimeSlot.overlaps()`, `Owner.block_time()`, `Owner.get_available_times()` | Supports `Recurrence` enums (`DAILY`, `WEEKLY`, `MONTHLY`). `TimeSlot.overlaps()` projects daily recurring events by time-of-day; `get_available_times()` subtracts recurring blocked times from the requested query window. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
