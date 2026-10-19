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


def test_suggest_time_slot_recurring_historical_date():
    historical_date = datetime(2024, 6, 1, 9, 0)
    current_date = datetime(2026, 10, 19, 0, 0)
    owner = Owner(
        name="Morgan",
        blocked_times=[
            TimeSlot(
                start_time=historical_date,
                duration=480,  # 09:00 to 17:00
                recurrence=Recurrence.DAILY,
                description="Work",
            )
        ],
    )
    scheduler = Scheduler(owner=owner)
    available = [TimeSlot(current_date, current_date + timedelta(days=1))]

    suggested = scheduler.suggest_time_slot(duration_minutes=60, available_times=available)
    assert suggested is not None
    assert suggested.start_time.year == 2026
    assert suggested.start_time == current_date


def test_owner_get_available_times_multi_day_and_weekly():
    start_date = datetime(2026, 10, 19, 0, 0)
    end_date = start_date + timedelta(days=3)
    owner = Owner(
        name="Taylor",
        blocked_times=[
            TimeSlot(
                start_time=start_date,
                duration=480,
                recurrence=Recurrence.DAILY,
                description="Sleep",
            ),
            TimeSlot(
                start_time=datetime(2024, 1, 2, 14, 0),  # Tuesday
                duration=60,
                recurrence=Recurrence.WEEKLY,
                description="Tuesday Meeting",
            ),
        ],
    )

    available = owner.get_available_times(start_date, end_date)
    tuesday_meeting = TimeSlot(datetime(2026, 10, 20, 14, 0), datetime(2026, 10, 20, 15, 0))
    for slot in available:
        assert not slot.overlaps(tuesday_meeting)


def test_timeslot_overlaps_overnight_daily():
    sleep_slot = TimeSlot(
        start_time=datetime(2026, 10, 19, 22, 0),
        duration=480,
        recurrence=Recurrence.DAILY,
    )
    late_task = TimeSlot(
        start_time=datetime(2026, 10, 19, 23, 0),
        duration=30,
    )
    early_task = TimeSlot(
        start_time=datetime(2026, 10, 20, 4, 0),
        duration=60,
    )
    day_task = TimeSlot(
        start_time=datetime(2026, 10, 19, 10, 0),
        duration=60,
    )

    assert sleep_slot.overlaps(late_task) is True
    assert late_task.overlaps(sleep_slot) is True
    assert sleep_slot.overlaps(early_task) is True
    assert early_task.overlaps(sleep_slot) is True
    assert sleep_slot.overlaps(day_task) is False
    assert day_task.overlaps(sleep_slot) is False


def test_scheduler_sort_by_time_and_filtering():
    scheduler = Scheduler()
    dog = Pet(name="Mochi", species="Dog", breed="Shiba")
    cat = Pet(name="Luna", species="Cat", breed="Siamese")

    t1 = Task(
        description="Morning Walk",
        time=datetime(2026, 10, 19, 8, 30),
        pet=dog,
        is_completed=True,
    )
    t2 = Task(
        description="Evening Feed",
        time=datetime(2026, 10, 19, 18, 0),
        pet=dog,
        is_completed=False,
    )
    t3 = Task(
        description="Cat Meds",
        time=datetime(2026, 10, 19, 7, 0),
        pet=cat,
        is_completed=False,
    )

    all_tasks = [t2, t1, t3]

    # 1. Pure sort by time
    sorted_all = scheduler.sort_by_time(all_tasks)
    assert sorted_all == [t3, t1, t2]

    # 2. Filter by pet name string
    dog_tasks = scheduler.sort_by_time(all_tasks, pet="Mochi")
    assert dog_tasks == [t1, t2]

    # 3. Filter by Pet object
    cat_tasks = scheduler.sort_by_time(all_tasks, pet=cat)
    assert cat_tasks == [t3]

    # 4. Filter by completion status (pending only)
    pending_tasks = scheduler.sort_by_time(all_tasks, is_completed=False)
    assert pending_tasks == [t3, t2]

    # 5. Filter by completion status (completed only)
    completed_tasks = scheduler.sort_by_time(all_tasks, is_completed=True)
    assert completed_tasks == [t1]


def test_scheduler_sort_by_time_string_format():
    scheduler = Scheduler()
    t1 = Task(description="Late walk", time=datetime(2026, 10, 19, 14, 0))
    t1.time = "14:00"
    t2 = Task(description="Early feed", time=datetime(2026, 10, 19, 8, 30))
    t2.time = "08:30"
    t3 = Task(description="Midday play", time=datetime(2026, 10, 19, 12, 15))
    t3.time = "12:15"

    sorted_tasks = scheduler.sort_by_time([t1, t2, t3])
    assert sorted_tasks == [t2, t3, t1]


def test_recurring_task_daily_completion_creates_next_instance():
    dog = Pet(name="Mochi", species="Dog", breed="Shiba")
    start = datetime(2026, 10, 19, 8, 30)
    task = Task(
        description="Daily Morning Walk",
        due_date=start,
        priority=Priority.HIGH,
        type=TaskType.WALKS,
        pet=dog,
        duration=30,
        recurrence=Recurrence.DAILY,
    )
    dog.add_task(task)
    assert len(dog.tasks) == 1

    next_task = task.mark_complete()
    assert task.is_completed is True
    assert next_task is not None
    assert next_task.due_date == start + timedelta(days=1)
    assert next_task.due_date.time() == start.time()
    assert next_task.is_completed is False
    assert next_task.recurrence == Recurrence.DAILY
    assert next_task.description == "Daily Morning Walk"
    assert next_task.pet is dog
    # Auto-registered to pet
    assert len(dog.tasks) == 2
    assert dog.tasks[-1] is next_task

    # Idempotent call does not spawn another occurrence
    duplicate = task.mark_complete()
    assert duplicate is None
    assert len(dog.tasks) == 2


def test_recurring_task_weekly_completion_creates_next_instance():
    cat = Pet(name="Luna", species="Cat", breed="Siamese")
    start = datetime(2026, 10, 19, 15, 0)
    task = Task(
        description="Weekly Grooming",
        due_date=start,
        priority=Priority.MEDIUM,
        type=TaskType.GROOMING,
        pet=cat,
        duration=45,
        recurrence=Recurrence.WEEKLY,
    )
    cat.add_task(task)

    next_task = task.mark_complete()
    assert task.is_completed is True
    assert next_task is not None
    assert next_task.due_date == start + timedelta(weeks=1)
    assert next_task.is_completed is False
    assert len(cat.tasks) == 2


def test_non_recurring_task_completion_creates_no_instance():
    task = Task(
        description="Vet Checkup",
        due_date=datetime(2026, 10, 19, 11, 0),
        recurrence=None,
    )
    next_task = task.mark_complete()
    assert task.is_completed is True
    assert next_task is None


def test_scheduler_complete_task_registers_next_instance():
    scheduler = Scheduler()
    start = datetime(2026, 10, 19, 9, 0)
    task = Task(
        description="Unassigned Daily Task",
        due_date=start,
        recurrence=Recurrence.DAILY,
    )
    scheduler.schedule_task(task)
    assert len(scheduler.tasks) == 1

    next_task = scheduler.complete_task(task)
    assert task.is_completed is True
    assert next_task is not None
    assert next_task.due_date == start + timedelta(days=1)
    assert len(scheduler.tasks) == 2
    assert scheduler.tasks[-1] is next_task


def test_scheduler_conflict_warnings_same_pet():
    scheduler = Scheduler()
    dog = Pet(name="Pochi", species="Dog", breed="Golden Retriever")
    t1 = Task(description="Walk", due_date=datetime(2026, 10, 19, 8, 30), duration=30, pet=dog)
    t2 = Task(description="Feed", due_date=datetime(2026, 10, 19, 8, 30), duration=15, pet=dog)
    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)

    warnings = scheduler.get_conflict_warnings()
    assert len(warnings) == 1
    assert "Same-Pet Conflict" in warnings[0]
    assert "Pochi is double-booked" in warnings[0]


def test_scheduler_conflict_warnings_concurrent_pets():
    scheduler = Scheduler()
    dog = Pet(name="Pochi", species="Dog", breed="Golden Retriever")
    cat = Pet(name="Tama", species="Cat", breed="Russian Blue")
    t1 = Task(description="Dog Walk", due_date=datetime(2026, 10, 19, 10, 0), duration=30, pet=dog)
    t2 = Task(description="Cat Feed", due_date=datetime(2026, 10, 19, 10, 15), duration=15, pet=cat)
    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)

    warnings = scheduler.get_conflict_warnings()
    assert len(warnings) == 1
    assert "Concurrent Care Conflict" in warnings[0]
    assert "Overlapping pet tasks" in warnings[0]


def test_scheduler_no_conflict_warnings():
    scheduler = Scheduler()
    dog = Pet(name="Pochi", species="Dog", breed="Golden Retriever")
    t1 = Task(description="Morning Walk", due_date=datetime(2026, 10, 19, 8, 0), duration=30, pet=dog)
    t2 = Task(description="Evening Walk", due_date=datetime(2026, 10, 19, 18, 0), duration=30, pet=dog)
    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)

    warnings = scheduler.get_conflict_warnings()
    assert warnings == []


def test_timeslot_overlaps_weekly_and_monthly():
    # Weekly slot: Tuesday 2026-10-13 14:00 to 15:00
    weekly_slot = TimeSlot(
        start_time=datetime(2026, 10, 13, 14, 0),
        duration=60,
        recurrence=Recurrence.WEEKLY,
    )
    # Overlapping slot on next Tuesday 2026-10-20 14:30-15:30
    next_tuesday_slot = TimeSlot(
        start_time=datetime(2026, 10, 20, 14, 30),
        duration=60,
    )
    # Non-overlapping slot on Wednesday 2026-10-21 14:00-15:00
    wednesday_slot = TimeSlot(
        start_time=datetime(2026, 10, 21, 14, 0),
        duration=60,
    )
    assert weekly_slot.overlaps(next_tuesday_slot) is True
    assert next_tuesday_slot.overlaps(weekly_slot) is True
    assert weekly_slot.overlaps(wednesday_slot) is False
    assert wednesday_slot.overlaps(weekly_slot) is False

    # Monthly slot: 15th of month 10:00 to 11:00 starting 2026-09-15
    monthly_slot = TimeSlot(
        start_time=datetime(2026, 9, 15, 10, 0),
        duration=60,
        recurrence=Recurrence.MONTHLY,
    )
    # Overlapping slot on next month 2026-10-15 10:30-11:30
    next_month_slot = TimeSlot(
        start_time=datetime(2026, 10, 15, 10, 30),
        duration=60,
    )
    # Non-overlapping slot on 2026-10-16 10:00-11:00
    different_day_slot = TimeSlot(
        start_time=datetime(2026, 10, 16, 10, 0),
        duration=60,
    )
    assert monthly_slot.overlaps(next_month_slot) is True
    assert next_month_slot.overlaps(monthly_slot) is True
    assert monthly_slot.overlaps(different_day_slot) is False
    assert different_day_slot.overlaps(monthly_slot) is False

    # Both recurring: Weekly vs Weekly
    weekly_same_day = TimeSlot(
        start_time=datetime(2026, 10, 20, 14, 30),
        duration=30,
        recurrence=Recurrence.WEEKLY,
    )
    weekly_diff_day = TimeSlot(
        start_time=datetime(2026, 10, 21, 14, 0),
        duration=60,
        recurrence=Recurrence.WEEKLY,
    )
    assert weekly_slot.overlaps(weekly_same_day) is True
    assert weekly_same_day.overlaps(weekly_slot) is True
    assert weekly_slot.overlaps(weekly_diff_day) is False

    # Both recurring: Monthly vs Monthly
    monthly_same_day = TimeSlot(
        start_time=datetime(2026, 10, 15, 10, 30),
        duration=30,
        recurrence=Recurrence.MONTHLY,
    )
    monthly_diff_day = TimeSlot(
        start_time=datetime(2026, 10, 16, 10, 0),
        duration=60,
        recurrence=Recurrence.MONTHLY,
    )
    assert monthly_slot.overlaps(monthly_same_day) is True
    assert monthly_same_day.overlaps(monthly_slot) is True
    assert monthly_slot.overlaps(monthly_diff_day) is False


def test_daily_recurrence_does_not_overlap_or_block_prior_dates():
    start_dt = datetime(2026, 10, 19, 9, 0)
    daily_slot = TimeSlot(
        start_time=start_dt,
        duration=480,
        recurrence=Recurrence.DAILY,
    )
    prior_slot = TimeSlot(
        start_time=datetime(2026, 10, 18, 10, 0),
        duration=60,
    )
    same_day_slot = TimeSlot(
        start_time=datetime(2026, 10, 19, 10, 0),
        duration=60,
    )
    future_day_slot = TimeSlot(
        start_time=datetime(2026, 10, 20, 10, 0),
        duration=60,
    )

    assert daily_slot.overlaps(prior_slot) is False
    assert prior_slot.overlaps(daily_slot) is False
    assert daily_slot.overlaps(same_day_slot) is True
    assert daily_slot.overlaps(future_day_slot) is True

    # Owner blocked times does not block dates prior to start date
    owner = Owner(name="Jordan", blocked_times=[daily_slot])
    avail_prior = owner.get_available_times(
        datetime(2026, 10, 17, 0, 0), datetime(2026, 10, 18, 0, 0)
    )
    assert len(avail_prior) == 1
    assert avail_prior[0].start_time == datetime(2026, 10, 17, 0, 0)
    assert avail_prior[0].end_time == datetime(2026, 10, 18, 0, 0)


def test_petless_and_newly_added_pet_tasks_in_owner_and_scheduler():
    owner = Owner(name="Alex")
    today = datetime.now()

    # Pet-less task scheduled directly on owner
    petless_task = Task(description="Buy pet shampoo", due_date=today, pet=None)
    owner.schedule_task(petless_task)

    assert petless_task in owner.get_all_tasks()
    todays_tasks = owner.scheduler.see_todays_tasks()
    assert petless_task in todays_tasks

    # Task with a new pet not previously added to owner.pets
    new_pet = Pet(name="Coco", species="Dog", breed="Poodle")
    assert new_pet not in owner.pets

    pet_task = Task(description="Annual vaccination", due_date=today, pet=new_pet)
    owner.schedule_task(pet_task)

    assert new_pet in owner.pets
    assert pet_task in new_pet.tasks
    assert pet_task in owner.get_all_tasks()
    todays_tasks_after = owner.scheduler.see_todays_tasks()
    assert pet_task in todays_tasks_after


def test_string_time_assignment_sort_by_time_and_end_time():
    scheduler = Scheduler()
    base_date = datetime(2026, 10, 19, 10, 0)

    # String time in constructor
    t_str = Task(description="Task from str", time="14:00")
    assert isinstance(t_str.due_date, datetime)
    assert t_str.due_date.hour == 14
    assert t_str.due_date.minute == 0
    assert isinstance(t_str.end_time, datetime)
    assert t_str.end_time == t_str.due_date + timedelta(minutes=t_str.duration)

    # Property setter with string time preserves base date
    t_prop = Task(description="Task setter", due_date=base_date)
    t_prop.time = "09:15"
    assert isinstance(t_prop.due_date, datetime)
    assert t_prop.due_date.date() == base_date.date()
    assert t_prop.due_date.hour == 9
    assert t_prop.due_date.minute == 15
    assert isinstance(t_prop.end_time, datetime)

    # Mixed list of tasks: datetime vs string assigned
    t1 = Task(description="Walk", due_date=datetime(2026, 10, 19, 16, 0))
    t2 = Task(description="Feed", due_date=datetime(2026, 10, 19, 8, 0))
    t2.time = "08:00"
    t3 = Task(description="Groom", due_date=datetime(2026, 10, 19, 12, 0))

    sorted_tasks = scheduler.sort_by_time([t1, t2, t3])
    assert sorted_tasks == [t2, t3, t1]


def test_scheduler_complete_task_recurring_pet_none_and_auto_adds_pet():
    owner = Owner(name="Sam")
    today = datetime.now()

    # Recurring task with pet=None
    petless_recurring = Task(
        description="Filter change",
        due_date=today,
        recurrence=Recurrence.DAILY,
        pet=None,
    )
    owner.schedule_task(petless_recurring)

    next_task = owner.scheduler.complete_task(petless_recurring)
    assert petless_recurring.is_completed is True
    assert next_task is not None
    assert next_task.is_completed is False
    assert next_task.pet is None
    assert next_task in owner.scheduler.tasks
    assert next_task in owner.get_all_tasks()

    # Recurring task with a new pet not in owner.pets adds pet to owner.pets
    unregistered_pet = Pet(name="Nemo", species="Fish", breed="Clownfish")
    assert unregistered_pet not in owner.pets

    fish_task = Task(
        description="Clean tank",
        due_date=today,
        recurrence=Recurrence.WEEKLY,
        pet=unregistered_pet,
    )
    next_fish_task = owner.scheduler.complete_task(fish_task)
    assert next_fish_task is not None
    assert unregistered_pet in owner.pets
    assert next_fish_task in unregistered_pet.tasks
    assert next_fish_task in owner.get_all_tasks()


def test_overnight_daily_inception_no_morning_conflict():
    sleep_slot = TimeSlot(
        start_time=datetime(2026, 10, 19, 22, 0),
        duration=480,
        recurrence=Recurrence.DAILY,
    )
    morning_slot = TimeSlot(
        start_time=datetime(2026, 10, 19, 4, 0),
        duration=60,
    )
    # Morning of inception date must not overlap
    assert sleep_slot.overlaps(morning_slot) is False
    assert morning_slot.overlaps(sleep_slot) is False

    # Morning of following date must overlap
    following_morning = TimeSlot(
        start_time=datetime(2026, 10, 20, 4, 0),
        duration=60,
    )
    assert sleep_slot.overlaps(following_morning) is True
    assert following_morning.overlaps(sleep_slot) is True


def test_suggest_time_slot_not_in_past_today():
    today = datetime.now()
    today_start = datetime(today.year, today.month, today.day, 0, 0)
    owner = Owner(
        name="Jordan",
        blocked_times=[
            TimeSlot(
                start_time=today_start,
                duration=480,  # 00:00 - 08:00
                recurrence=Recurrence.DAILY,
            ),
            TimeSlot(
                start_time=today_start.replace(hour=9),
                duration=480,  # 09:00 - 17:00
                recurrence=Recurrence.DAILY,
            ),
        ],
    )
    scheduler = Scheduler(owner=owner)

    # Simulated 10:00 AM start ignores expired morning opening (08:00-09:00)
    simulated_start = today_start.replace(hour=10, minute=0)
    suggested = scheduler.suggest_time_slot(duration_minutes=30, search_start=simulated_start)
    assert suggested is not None
    assert suggested.start_time >= simulated_start
    assert suggested.start_time == today_start.replace(hour=17, minute=0)

    # Calling suggest_time_slot without search_start uses datetime.now() and never suggests past slots
    suggested_now = scheduler.suggest_time_slot(duration_minutes=30)
    if suggested_now is not None:
        assert suggested_now.end_time > datetime.now()


def test_scheduler_get_all_tasks_upcoming_only():
    scheduler = Scheduler()
    now = datetime.now()
    past_task = Task(
        description="Past Vet Visit",
        due_date=now - timedelta(days=2),
        duration=30,
    )
    upcoming_task = Task(
        description="Future Grooming",
        due_date=now + timedelta(days=2),
        duration=45,
    )
    scheduler.schedule_task(past_task)
    scheduler.schedule_task(upcoming_task)

    all_tasks = scheduler.get_all_tasks(upcoming_only=False)
    assert len(all_tasks) == 2
    assert past_task in all_tasks
    assert upcoming_task in all_tasks

    upcoming_tasks = scheduler.get_all_tasks(upcoming_only=True)
    assert len(upcoming_tasks) == 1
    assert upcoming_tasks[0] == upcoming_task


def test_multi_day_slot_spanning_recurring_day_overlap():
    # Weekly recurring slot on Wednesday 14:00 - 15:00 (2026-10-14 is Wednesday)
    weekly_slot = TimeSlot(
        start_time=datetime(2026, 10, 14, 14, 0),
        duration=60,
        recurrence=Recurrence.WEEKLY,
    )
    # Multi-day non-recurring slot: Monday 2026-10-19 to Friday 2026-10-23
    multi_day_slot = TimeSlot(
        start_time=datetime(2026, 10, 19, 10, 0),
        end_time=datetime(2026, 10, 23, 10, 0),
    )
    # Multi-day slot spanning the weekend only (2026-10-24 Saturday to 2026-10-25 Sunday)
    weekend_slot = TimeSlot(
        start_time=datetime(2026, 10, 24, 8, 0),
        end_time=datetime(2026, 10, 25, 20, 0),
    )

    # Multi-day slot spans across Wednesday 2026-10-21
    assert weekly_slot.overlaps(multi_day_slot) is True
    assert multi_day_slot.overlaps(weekly_slot) is True

    # Weekend slot does not span Wednesday
    assert weekly_slot.overlaps(weekend_slot) is False
    assert weekend_slot.overlaps(weekly_slot) is False


def test_scheduler_sort_by_priority():
    scheduler = Scheduler()
    base = datetime(2026, 10, 19, 10, 0)
    task_low = Task(
        description="Low Early",
        due_date=base,
        priority=Priority.LOW,
    )
    task_high = Task(
        description="High Late",
        due_date=base + timedelta(hours=2),
        priority=Priority.HIGH,
    )
    task_med = Task(
        description="Med Mid",
        due_date=base + timedelta(hours=1),
        priority=Priority.MEDIUM,
    )
    sorted_tasks = scheduler.sort_by_priority([task_low, task_high, task_med])
    assert sorted_tasks == [task_high, task_med, task_low]






