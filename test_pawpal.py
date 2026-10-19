from datetime import datetime, timedelta
import pytest
from pawpal_system import Priority, TaskType, Recurrence, TimeSlot, Pet, Task, Owner, Scheduler


def test_task_attributes_and_properties():
    now = datetime.now()
    task = Task(
        description="Morning Walk",
        due_date=now,
        priority=Priority.HIGH,
        type=TaskType.WALKS,
        duration=30,
        recurrence=Recurrence.DAILY,
    )
    assert task.description == "Morning Walk"
    assert task.time == now
    assert task.frequency == Recurrence.DAILY
    assert task.completion_status is False
    task.execute()
    assert task.completion_status is True
    assert task.is_completed is True


def test_pet_task_management():
    pet = Pet(name="Mochi", species="Dog", breed="Shiba")
    task = Task(description="Grooming", type=TaskType.GROOMING)
    pet.add_task(task)
    assert task in pet.tasks
    assert task.pet == pet
    assert len(pet.get_tasks()) == 1


def test_owner_multi_pet_get_all_tasks():
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="Dog", breed="Shiba")
    cat = Pet(name="Luna", species="Cat", breed="Siamese")
    owner.add_pet(dog)
    owner.add_pet(cat)

    task_dog = Task(description="Walk dog", pet=dog)
    task_cat = Task(description="Feed cat", pet=cat)
    dog.add_task(task_dog)
    cat.add_task(task_cat)

    all_tasks = owner.get_all_tasks()
    assert len(all_tasks) == 2
    assert task_dog in all_tasks
    assert task_cat in all_tasks


def test_scheduler_reads_from_owner():
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="Dog", breed="Shiba")
    cat = Pet(name="Luna", species="Cat", breed="Siamese")
    owner.add_pet(dog)
    owner.add_pet(cat)

    now = datetime.now()
    task_dog = Task(description="Walk dog", due_date=now,
                    priority=Priority.LOW, pet=dog)
    task_cat = Task(description="Feed cat", due_date=now,
                    priority=Priority.HIGH, pet=cat)
    dog.add_task(task_dog)
    cat.add_task(task_cat)

    scheduler = Scheduler(owner=owner)
    todays_tasks = scheduler.see_todays_tasks()

    assert len(todays_tasks) == 2
    assert todays_tasks[0] == task_cat
    assert todays_tasks[1] == task_dog


def test_timeslot_overlaps():
    base = datetime(2026, 10, 19, 10, 0)
    slot1 = TimeSlot(base, base + timedelta(hours=1))
    slot_overlap = TimeSlot(base + timedelta(minutes=30),
                            base + timedelta(minutes=90))
    slot_contained = TimeSlot(
        base + timedelta(minutes=15), base + timedelta(minutes=45))
    slot_adjacent = TimeSlot(base + timedelta(hours=1),
                             base + timedelta(hours=2))
    slot_disjoint = TimeSlot(base + timedelta(hours=2),
                             base + timedelta(hours=3))

    assert slot1.overlaps(slot_overlap) is True
    assert slot_overlap.overlaps(slot1) is True
    assert slot1.overlaps(slot_contained) is True
    assert slot_contained.overlaps(slot1) is True
    assert slot1.overlaps(slot_adjacent) is False
    assert slot_adjacent.overlaps(slot1) is False
    assert slot1.overlaps(slot_disjoint) is False
    assert slot_disjoint.overlaps(slot1) is False


def test_alert_conflict_includes_blocked_times():
    base = datetime(2026, 10, 19, 10, 0)
    blocked = TimeSlot(base, base + timedelta(minutes=60))
    owner = Owner(name="Jordan", blocked_times=[blocked])
    pet = Pet(name="Mochi", species="Dog", breed="Shiba")
    owner.add_pet(pet)

    task = Task(description="Walk", due_date=base +
                timedelta(minutes=30), duration=30, pet=pet)
    pet.add_task(task)

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.alert_conflict()

    assert len(conflicts) == 1
    assert conflicts[0] == (task, blocked)


def test_suggest_time_slot_skips_blocked_times():
    base = datetime(2026, 10, 19, 9, 0)
    available = [TimeSlot(base, base + timedelta(hours=3))]
    blocked = [TimeSlot(base, base + timedelta(minutes=30))]
    owner = Owner(name="Jordan", available_times=available,
                  blocked_times=blocked)
    scheduler = Scheduler(owner=owner)

    suggested = scheduler.suggest_time_slot(duration_minutes=30)
    assert suggested is not None
    assert suggested.start_time == base + timedelta(minutes=30)
    assert suggested.end_time == base + timedelta(minutes=60)


def test_owner_schedule_task_without_explicit_scheduler():
    owner = Owner(name="Alex")
    dog = Pet(name="Rusty", species="Dog", breed="Labrador")
    owner.add_pet(dog)
    task = Task(description="Evening walk", pet=dog)

    owner.schedule_task(task)

    assert task in owner.get_all_tasks()
    assert task in owner.scheduler.tasks


def test_owner_get_available_times_from_blocked_times():
    base_date = datetime(2026, 10, 19, 0, 0)
    end_date = base_date + timedelta(days=1)
    owner = Owner(
        name="Sam",
        blocked_times=[
            TimeSlot(
                start_time=base_date,
                duration=480,
                recurrence=Recurrence.DAILY,
                description="Sleep",
            ),
            TimeSlot(
                start_time=base_date.replace(hour=9),
                duration=480,
                recurrence=Recurrence.DAILY,
                description="Work",
            ),
        ],
    )

    available = owner.get_available_times(base_date, end_date)
    # Available should be 08:00-09:00 (60 min) and 17:00-24:00 (420 min)
    assert len(available) == 2
    assert available[0].start_time == base_date.replace(hour=8)
    assert available[0].end_time == base_date.replace(hour=9)
    assert available[1].start_time == base_date.replace(hour=17)
    assert available[1].end_time == end_date


def test_organize_tasks_due_date_precedence():
    scheduler = Scheduler()
    base = datetime(2026, 10, 19, 10, 0)
    task_early_low = Task(
        description="Low priority early",
        due_date=base,
        priority=Priority.LOW,
    )
    task_late_high = Task(
        description="High priority late",
        due_date=base + timedelta(hours=1),
        priority=Priority.HIGH,
    )
    task_early_high = Task(
        description="High priority early",
        due_date=base,
        priority=Priority.HIGH,
    )

    # Earlier due_date must rank ahead of higher priority later due_date.
    # When due_dates match, higher priority ranks first.
    ordered = scheduler.organize_tasks([task_late_high, task_early_low, task_early_high])
    assert ordered == [task_early_high, task_early_low, task_late_high]


def test_task_mark_complete():
    task = Task(description="Evening feeding", type=TaskType.FEEDINGS)
    assert task.is_completed is False
    assert task.completion_status is False

    task.mark_complete()
    assert task.is_completed is True
    assert task.completion_status is True

    # Idempotent call
    task.mark_complete()
    assert task.is_completed is True


def test_pet_task_addition_count_increase():
    pet = Pet(name="Mochi", species="Dog", breed="Shiba")
    assert len(pet.get_tasks()) == 0

    task1 = Task(description="Walk", type=TaskType.WALKS)
    pet.add_task(task1)
    assert len(pet.get_tasks()) == 1

    task2 = Task(description="Dinner", type=TaskType.FEEDINGS)
    pet.add_task(task2)
    assert len(pet.get_tasks()) == 2

    # Duplicate addition should not increase count
    pet.add_task(task1)
    assert len(pet.get_tasks()) == 2

