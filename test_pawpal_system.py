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
    task_dog = Task(description="Walk dog", due_date=now, priority=Priority.LOW, pet=dog)
    task_cat = Task(description="Feed cat", due_date=now, priority=Priority.HIGH, pet=cat)
    dog.add_task(task_dog)
    cat.add_task(task_cat)

    scheduler = Scheduler(owner=owner)
    todays_tasks = scheduler.see_todays_tasks()

    assert len(todays_tasks) == 2
    assert todays_tasks[0] == task_cat
    assert todays_tasks[1] == task_dog
