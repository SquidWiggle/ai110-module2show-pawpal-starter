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

An example usage demonstrating sorting, filtering, and conflict detection is in `main.py`:

1. Define pets Tama (cat) and Pochi (dog) with required care types.
2. Configure Owner with recurring daily Work and Sleep blackout intervals.
3. Schedule 7 tasks out of chronological order with intentional conflicts (same-pet clash, concurrent-care clash, and owner blackout clash).
4. Demonstrate chronological sorting, pet filtering, and status filtering.
5. Generate automated conflict detection warnings.

Run `main.py`:
```bash
python3 main.py
```
```text
--- 1. Raw Unsorted Tasks (As Added) ---
Time              Task            Pet      Status      Priority
--------------------------------------------------------------
2024-06-01 08:00  Feed Tama       Tama     Completed   HIGH
2024-06-01 07:30  Tama Medicine   Tama     Pending     HIGH
2024-06-01 19:00  Feed Tama (Clash) Tama   Pending     MEDIUM
2024-06-01 19:00  Evening Walk    Pochi    Pending     MEDIUM
2024-06-01 14:00  Play Pochi      Pochi    Completed   LOW
2024-06-01 08:30  Feed Pochi      Pochi    Pending     HIGH
2024-06-01 08:30  Morning Walk (Clash) Pochi Pending   HIGH

--- 2. All Tasks Sorted by Time ---
Time              Task            Pet      Status      Priority
--------------------------------------------------------------
2024-06-01 07:30  Tama Medicine   Tama     Pending     HIGH
2024-06-01 08:00  Feed Tama       Tama     Completed   HIGH
2024-06-01 08:30  Feed Pochi      Pochi    Pending     HIGH
2024-06-01 08:30  Morning Walk (Clash) Pochi Pending   HIGH
2024-06-01 14:00  Play Pochi      Pochi    Completed   LOW
2024-06-01 19:00  Feed Tama (Clash) Tama   Pending     MEDIUM
2024-06-01 19:00  Evening Walk    Pochi    Pending     MEDIUM

--- 3. Filtered: Tama Only (Sorted by Time) ---
Time              Task            Pet      Status      Priority
--------------------------------------------------------------
2024-06-01 07:30  Tama Medicine   Tama     Pending     HIGH
2024-06-01 08:00  Feed Tama       Tama     Completed   HIGH
2024-06-01 19:00  Feed Tama (Clash) Tama   Pending     MEDIUM

--- 4. Filtered: Pending Only (Sorted by Time) ---
Time              Task            Pet      Status      Priority
--------------------------------------------------------------
2024-06-01 07:30  Tama Medicine   Tama     Pending     HIGH
2024-06-01 08:30  Feed Pochi      Pochi    Pending     HIGH
2024-06-01 08:30  Morning Walk (Clash) Pochi Pending   HIGH
2024-06-01 19:00  Feed Tama (Clash) Tama   Pending     MEDIUM
2024-06-01 19:00  Evening Walk    Pochi    Pending     MEDIUM

--- 5. Filtered: Pochi Completed Only ---
Time              Task            Pet      Status      Priority
--------------------------------------------------------------
2024-06-01 14:00  Play Pochi      Pochi    Completed   LOW

--- 6. Conflict Detection Warnings ---
⚠️ [Concurrent Care Conflict] Overlapping pet tasks: Tama ('Feed Tama (Clash)') and Pochi ('Evening Walk') overlap around 19:00 - 19:15.
⚠️ [Same-Pet Conflict] Pochi is double-booked: 'Feed Pochi' and 'Morning Walk (Clash)' overlap around 08:30 - 08:45.
⚠️ [Blocked Time Collision] Tama task 'Tama Medicine' collides with owner's Sleep schedule.
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
collecting ... collected 34 items

test_pawpal.py ..................................                        [100%]

============================== 34 passed in 0.04s ==============================
```

## 📐 Smarter Scheduling

The scheduling engine combines multi-pet aggregation, constraint-aware slot finding, and conflict resolution across owners and pets.

### Feature Overview

| Feature | Method(s) | Notes |
|---|---|---|
| **Sorting by Time & Priority** | `Scheduler.sort_by_time()`, `Scheduler.organize_tasks()` | Primary sort by `due_date`; secondary tie-break by priority weight (`HIGH: 0`, `MEDIUM: 1`, `LOW: 2`). |
| **Conflict Warnings** | `Scheduler.get_conflict_warnings()`, `Scheduler.alert_conflict()`, `TimeSlot.overlaps()` | Pairwise $O(N^2)$ interval overlap check (`start1 < end2` and `start2 < end1`) detecting same-pet, concurrent-pet, and owner blackout collisions. |
| **Daily & Periodic Recurrence** | `Task.mark_complete()`, `Scheduler.complete_task()`, `Owner.get_available_times()` | Automatically creates the next due task (+1 day, +7 days, +30 days) whenever a recurring task is completed, and applies recurring owner busy hours. |
| **Smart Slot Suggestion** | `Scheduler.suggest_time_slot()` | First-fit interval search stepping by 15-minute increments against existing tasks and recurring owner blocked times. |
| **Multi-Pet Task Filtering** | `Scheduler.see_todays_tasks()`, `Owner.get_all_tasks()` | Aggregates all pet tasks under an owner and filters by calendar date, pet identity, or completion status. |

### Feature Documentation

1. **Sorting by Time & Priority**
   - **What it does**: Orders tasks chronologically while prioritizing urgent pet care (e.g. high-priority medication before low-priority grooming).
   - **How it works**: Uses a composite sort key `(task.due_date, priority_weight)`. `Scheduler.sort_by_time` handles standard chronological views; `Scheduler.organize_tasks` applies the secondary priority tie-breaker.

2. **Conflict Warnings**
   - **What it does**: Flags scheduling collisions before they happen and labels the collision type with human-readable alerts.
   - **How it works**: Checks all pairs of active tasks and owner busy times for overlapping hours (`start1 < end2 and start2 < end1`). Categorizes into 3 warning types:
     - `Same-Pet Conflict`: Same pet double-booked for two activities at once.
     - `Concurrent Care Conflict`: Two different pets requiring simultaneous attention from one owner.
     - `Blocked Time Collision`: Pet task scheduled during owner sleep, work, or blackout hours.

3. **Daily Recurrence**
   - **What it does**: Automatically schedules the next occurrence when recurring care (like daily feeding) is completed, and enforces recurring owner blackout schedules.
   - **How it works**: On `task.mark_complete()`, calculates the next due date based on the recurrence rule (`DAILY` $\rightarrow$ +1 day, `WEEKLY` $\rightarrow$ +7 days, `MONTHLY` $\rightarrow$ +30 days), instantiates a fresh uncompleted task, and links it back to the pet and scheduler.

4. **Smart Slot Suggestion**
   - **What it does**: Automatically finds the next available open time window for a task of a given duration.
   - **How it works**: Performs a first-fit linear scan through owner free intervals, testing prospective windows in 15-minute increments. Skips past any interval that overlaps an active task or projected recurring blackout block until a collision-free window is found.

5. **Multi-Pet Task Filtering**
   - **What it does**: Lets owners isolate tasks by day, pet, or completion status across their entire household.
   - **How it works**: Deduplicates tasks across registered pets and scheduler queues, applying date matching (`task.due_date.date() == check_date`) and optional pet name / completion status filters.



## 📸 Demo Walkthrough

1. **Set Your Routine & Add Pets (Sidebar)**
   - Review your built-in busy hours (Sleep `00:00 - 08:00` and Work `09:00 - 17:00`), or add new blackout blocks.
   - Open **Add New Pet** to register your pets (e.g., name: "Mochi", species: "Dog", breed: "Shiba Inu").

2. **Schedule Pet Care Tasks (Sidebar)**
   - Choose a pet and pick a care type (`FEEDINGS`, `WALKS`, `MEDICATIONS`, etc.).
   - Set start time, duration in minutes, priority (`HIGH`, `MEDIUM`, `LOW`), and recurrence (`DAILY`, `WEEKLY`, or `MONTHLY`).
   - Click **Schedule Task** to add it to the planner.

3. **Check Real-Time Conflict Alerts**
   - The scheduler checks for schedule clashes and displays warnings:
     - **Same-Pet Conflict**: One pet is double-booked for two activities at once.
     - **Concurrent Care Conflict**: Two different pets need you at the exact same time.
     - **Blocked Time Collision**: A task falls during your sleep or work hours.

4. **View and Sort Your Daily Schedule**
   - Switch between **Target Date** (view today's tasks) and **All Upcoming**.
   - Filter by a specific pet or completion status (Pending vs. Completed).
   - Sort by **Time (Chronological)** to see what comes next, or by **Priority (High → Low)** to handle urgent care first.

5. **Complete Tasks & Find Open Slots (Cards & Slot Finder)**
   - Click **Mark Complete** on any task. If marked daily, the scheduler automatically schedules the next occurrence for tomorrow.
   - Need to fit in a last-minute activity? Enter duration in the **Open Time Slot Finder** at the bottom to get the earliest conflict-free opening.
