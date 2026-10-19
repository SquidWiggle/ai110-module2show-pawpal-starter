from datetime import datetime

from pawpal_system import (
    Pet, Owner, Scheduler, Task, TaskType, Priority, TimeSlot
)


def main():
    cat = Pet('Tama', 'cat', 'Russian Blue', [
        TaskType.FEEDINGS, TaskType.VET_APPOINTMENT, TaskType.GROOMING])
    dog_1 = Pet('Pochi', 'dog', 'Golden Retriever', [
        TaskType.FEEDINGS, TaskType.WALKS, TaskType.PLAY, TaskType.GROOMING])
    feed_cat = Task(
        description='Feed Tama',
        due_date=datetime(2024, 6, 1, 8, 0),
        priority=Priority.HIGH,
        type=TaskType.FEEDINGS,
        pet=cat,
        duration=15,
        is_completed=False,
    )
    feed_dog = Task(
        description='Feed Pochi',
        due_date=datetime(2024, 6, 1, 8, 30),
        priority=Priority.HIGH,
        type=TaskType.FEEDINGS,
        pet=dog_1,
        duration=15,
        is_completed=False,
    )
    walk_dog = Task(
        description='Walk Pochi',
        due_date=datetime(2024, 6, 1, 10, 0),
        priority=Priority.MEDIUM,
        type=TaskType.WALKS,
        pet=dog_1,
        duration=30,
        is_completed=False,
    )
    owner_1 = Owner(name='John Doe', available_times=[TimeSlot(start_time=datetime(2024, 6, 1, 9, 0), end_time=datetime(2024, 6, 1, 17, 0))], pets=[cat, dog_1])
    owner_1.add_pet(cat)
    owner_1.add_pet(dog_1)
    scheduler = Scheduler()

    owner_1.schedule_task(scheduler, feed_cat)
    owner_1.schedule_task(scheduler, feed_dog)
    owner_1.schedule_task(scheduler, walk_dog)
    print("Scheduled Tasks:")
    print(f"{'Time':<17} {'Task':<15} {'Pet':<10} {'Duration':<10} {'Priority'}")
    print("-" * 60)
    for task in owner_1.get_all_tasks():
        pet_name = task.pet.name if task.pet else "N/A"
        time_str = task.due_date.strftime("%Y-%m-%d %H:%M")
        print(f"{time_str:<17} {task.description:<15} {pet_name:<10} {f'{task.duration}m':<10} {task.priority.value}")


if __name__ == "__main__":
    main()

