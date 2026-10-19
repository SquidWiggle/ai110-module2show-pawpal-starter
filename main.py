from datetime import datetime

from pawpal_system import (
    Pet, Owner, Task, TaskType, Priority, Recurrence, TimeSlot
)


def _print_tasks(title: str, tasks: list[Task]) -> None:
    print(f"\n--- {title} ---")
    print(f"{'Time':<17} {'Task':<15} {'Pet':<8} {'Status':<11} {'Priority'}")
    print("-" * 62)
    for task in tasks:
        pet_name = task.pet.name if task.pet else "N/A"
        time_str = task.due_date.strftime("%Y-%m-%d %H:%M")
        status_str = "Completed" if task.is_completed else "Pending"
        print(f"{time_str:<17} {task.description:<15} {pet_name:<8} {status_str:<11} {task.priority.value}")


def main():
    cat = Pet('Tama', 'cat', 'Russian Blue', [
        TaskType.FEEDINGS, TaskType.VET_APPOINTMENT, TaskType.GROOMING])
    dog_1 = Pet('Pochi', 'dog', 'Golden Retriever', [
        TaskType.FEEDINGS, TaskType.WALKS, TaskType.PLAY, TaskType.GROOMING])

    owner_1 = Owner(
        name='John Doe',
        pets=[cat, dog_1],
        blocked_times=[
            TimeSlot(
                start_time=datetime(2024, 6, 1, 0, 0),
                duration=480,
                recurrence=Recurrence.DAILY,
                description='Sleep',
            ),
            TimeSlot(
                start_time=datetime(2024, 6, 1, 9, 0),
                duration=480,
                recurrence=Recurrence.DAILY,
                description='Work',
            ),
        ],
    )

    # 1. Define tasks out of chronological order with mixed status & pets
    t_evening_walk = Task(
        description='Evening Walk',
        due_date=datetime(2024, 6, 1, 19, 0),
        priority=Priority.MEDIUM,
        type=TaskType.WALKS,
        pet=dog_1,
        duration=30,
        is_completed=False,
    )
    t_morning_feed_cat = Task(
        description='Feed Tama',
        due_date=datetime(2024, 6, 1, 8, 0),
        priority=Priority.HIGH,
        type=TaskType.FEEDINGS,
        pet=cat,
        duration=15,
        is_completed=True,
    )
    t_afternoon_play = Task(
        description='Play Pochi',
        due_date=datetime(2024, 6, 1, 14, 0),
        priority=Priority.LOW,
        type=TaskType.PLAY,
        pet=dog_1,
        duration=20,
        is_completed=True,
    )
    t_early_med_cat = Task(
        description='Tama Medicine',
        due_date=datetime(2024, 6, 1, 7, 30),
        priority=Priority.HIGH,
        type=TaskType.MEDICATIONS,
        pet=cat,
        duration=10,
        is_completed=False,
    )
    t_morning_feed_dog = Task(
        description='Feed Pochi',
        due_date=datetime(2024, 6, 1, 8, 30),
        priority=Priority.HIGH,
        type=TaskType.FEEDINGS,
        pet=dog_1,
        duration=15,
        is_completed=False,
    )
    # Conflicting task 1: Same pet (Pochi) double-booked at 08:30
    t_clash_dog_walk = Task(
        description='Morning Walk (Clash)',
        due_date=datetime(2024, 6, 1, 8, 30),
        priority=Priority.HIGH,
        type=TaskType.WALKS,
        pet=dog_1,
        duration=30,
        is_completed=False,
    )
    # Conflicting task 2: Concurrent pet care at 19:00 during Pochi's evening walk
    t_clash_cat_feed = Task(
        description='Feed Tama (Clash)',
        due_date=datetime(2024, 6, 1, 19, 0),
        priority=Priority.MEDIUM,
        type=TaskType.FEEDINGS,
        pet=cat,
        duration=15,
        is_completed=False,
    )

    # 2. Schedule tasks in scrambled order
    out_of_order_tasks = [
        t_evening_walk,
        t_morning_feed_cat,
        t_afternoon_play,
        t_early_med_cat,
        t_morning_feed_dog,
        t_clash_dog_walk,
        t_clash_cat_feed,
    ]
    for task in out_of_order_tasks:
        owner_1.schedule_task(task)

    # 3. Print verification views
    _print_tasks("1. Raw Unsorted Tasks (As Added)", owner_1.get_all_tasks())
    _print_tasks("2. All Tasks Sorted by Time",
                 owner_1.scheduler.sort_by_time())
    _print_tasks("3. Filtered: Tama Only (Sorted by Time)",
                 owner_1.scheduler.sort_by_time(pet="Tama"))
    _print_tasks("4. Filtered: Pending Only (Sorted by Time)",
                 owner_1.scheduler.sort_by_time(is_completed=False))
    _print_tasks("5. Filtered: Pochi Completed Only",
                 owner_1.scheduler.sort_by_time(pet=dog_1, is_completed=True))

    # 4. Conflict detection verification
    print("\n--- 6. Conflict Detection Warnings ---")
    warnings = owner_1.scheduler.get_conflict_warnings()
    if warnings:
        for warning in warnings:
            print(warning)
    else:
        print("No conflicts detected.")


if __name__ == "__main__":
    main()

