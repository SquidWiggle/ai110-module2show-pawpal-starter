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
platform darwin -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sameen/CodePath/ai110-module2show-pawpal-starter
collecting ... collected 24 items

test_pawpal.py ........................                                  [100%]

============================== 24 passed in 0.06s ==============================
```

## 📐 Smarter Scheduling

The scheduling engine combines multi-pet aggregation, constraint-aware slot finding, and conflict resolution across owners and pets.

### Feature Overview

| Feature | Method(s) | Summary |
|---|---|---|
| **Sorting behavior** | `Scheduler.sort_by_time()`, `Scheduler.organize_tasks()` | Chronological ordering by `due_date`/time with secondary sorting by priority (`HIGH: 0`, `MEDIUM: 1`, `LOW: 2`). |
| **Filtering behavior** | `Scheduler.sort_by_time()`, `Scheduler.see_todays_tasks()`, `Owner.get_all_tasks()` | Filters by pet, completion status, or date; aggregates tasks across all owned pets. |
| **Conflict detection logic** | `TimeSlot.overlaps()`, `Scheduler.alert_conflict()`, `Scheduler.get_conflict_warnings()`, `Scheduler.suggest_time_slot()` | Pairwise interval overlap checks with `itertools.combinations`; distinguishes same-pet, concurrent-care, and owner-blocked collisions. |
| **Recurring task logic** | `Task.mark_complete()`, `Scheduler.complete_task()`, `TimeSlot.overlaps()`, `Owner.get_available_times()` | Spawns successor occurrences on task completion (+1 day, +7 days, +30 days); projects recurring blackout windows across date ranges. |

### Feature Documentation

1. **Sorting Behavior**
   - `Scheduler.sort_by_time(tasks=None, owner=None, pet=None, is_completed=None)`: Chronologically sorts tasks by `Task.time` (supporting both `datetime` objects and `"HH:MM"` time strings).
   - `Scheduler.organize_tasks(tasks=None, owner=None)`: Sorts tasks primarily by chronological `due_date`, then secondarily by priority weight (`HIGH: 0`, `MEDIUM: 1`, `LOW: 2`).

2. **Filtering Behavior**
   - `Scheduler.sort_by_time()`: Filters tasks dynamically by `pet` (accepts `Pet` instance or string name) and by `is_completed` / `completion_status` boolean flag.
   - `Scheduler.see_todays_tasks(owner=None, target_date=None)`: Filters tasks matching a specific calendar date (defaults to today's date).
   - `Owner.get_all_tasks()`: Aggregates tasks across all pets registered to an owner.

3. **Conflict Detection Logic**
   - `TimeSlot.overlaps(other)`: Evaluates interval intersection ($s_1 < e_2 \text{ and } s_2 < e_1$), including daily recurrence time-of-day projection.
   - `Scheduler.alert_conflict(available_times=None, owner=None)`: Uses `itertools.combinations` to perform pairwise collision checks across all pending tasks and against owner `blocked_times`, returning `(task, conflict)` tuples.
   - `Scheduler.get_conflict_warnings(owner=None)` / `Scheduler.check_conflicts()`: Generates descriptive advisory warnings distinguishing same-pet double-booking, cross-pet concurrent duties, and owner blocked time collisions.
   - `Scheduler.suggest_time_slot(duration_minutes, available_times=None, owner=None)`: Scans available intervals to find the earliest non-colliding time slot.

4. **Recurring Task Logic**
   - `Task.mark_complete()` / `Task.execute()`: Auto-spawns the successor `Task` upon completion based on recurrence delta (`DAILY`: +1 day, `WEEKLY`: +7 days, `MONTHLY`: +30 days) and registers it to the pet.
   - `Scheduler.complete_task(task)`: Invokes `task.mark_complete()` and registers the generated successor task into `Scheduler.tasks`.
   - `Owner.get_available_times(start, end)`: Dynamically projects recurring blocked times (`DAILY`, `WEEKLY`, `MONTHLY`) across a requested query interval and slices free time intervals.



## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
