from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class Priority(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskType(Enum):
    FEEDINGS = "FEEDINGS"
    WALKS = "WALKS"
    MEDICATIONS = "MEDICATIONS"
    VET_APPOINTMENT = "VET_APPOINTMENT"
    PLAY = "PLAY"
    GROOMING = "GROOMING"


class Recurrence(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start_time < other.end_time and other.start_time < self.end_time



@dataclass
class Pet:
    name: str
    species: str
    breed: str
    required_care: list[TaskType] = field(default_factory=list)
    tasks: list["Task"] = field(default_factory=list)

    def add_task(self, task: "Task") -> None:
        if task not in self.tasks:
            self.tasks.append(task)
        if task.pet is not self:
            task.pet = self

    def get_tasks(self) -> list["Task"]:
        return list(self.tasks)


@dataclass
class Task:
    description: str = ""
    due_date: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.MEDIUM
    type: TaskType = TaskType.WALKS
    pet: Pet | None = None
    duration: int = 30
    recurrence: Recurrence | None = None
    is_completed: bool = False

    def __init__(
        self,
        description: str = "",
        due_date: datetime | None = None,
        priority: Priority | str = Priority.MEDIUM,
        type: TaskType | str = TaskType.WALKS,
        pet: Pet | None = None,
        duration: int = 30,
        recurrence: Recurrence | str | None = None,
        is_completed: bool = False,
        time: datetime | None = None,
        frequency: Recurrence | str | None = None,
        completion_status: bool | None = None,
    ):
        self.description = description
        self.due_date = due_date or time or datetime.now()

        if isinstance(priority, str):
            self.priority = Priority(priority.upper())
        else:
            self.priority = priority

        if isinstance(type, str):
            self.type = TaskType(type.upper())
        else:
            self.type = type

        self.pet = pet
        self.duration = duration

        rec = frequency if frequency is not None else recurrence
        if isinstance(rec, str):
            self.recurrence = Recurrence(rec.upper())
        else:
            self.recurrence = rec

        if completion_status is not None:
            self.is_completed = completion_status
        else:
            self.is_completed = is_completed

        if not self.description:
            self.description = self.type.value if hasattr(self.type, "value") else str(self.type)

    @property
    def time(self) -> datetime:
        return self.due_date

    @time.setter
    def time(self, val: datetime) -> None:
        self.due_date = val

    @property
    def frequency(self) -> Recurrence | None:
        return self.recurrence

    @frequency.setter
    def frequency(self, val: Recurrence | None) -> None:
        self.recurrence = val

    @property
    def completion_status(self) -> bool:
        return self.is_completed

    @completion_status.setter
    def completion_status(self, val: bool) -> None:
        self.is_completed = val

    @property
    def end_time(self) -> datetime:
        return self.due_date + timedelta(minutes=self.duration)

    @property
    def time_slot(self) -> TimeSlot:
        return TimeSlot(start_time=self.due_date, end_time=self.end_time)

    def execute(self) -> None:
        self.is_completed = True


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)
    available_times: list[TimeSlot] = field(default_factory=list)
    blocked_times: list[TimeSlot] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        if pet not in self.pets:
            self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        # Aggregate tasks across every pet
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def schedule_task(self, scheduler: "Scheduler", task: Task) -> None:
        if task.pet and task.pet in self.pets and task not in task.pet.tasks:
            task.pet.add_task(task)
        scheduler.schedule_task(task)

    def feed_pet(self, pet: Pet) -> None:
        feed_tasks = [t for t in pet.tasks if t.type == TaskType.FEEDINGS and not t.is_completed]
        if feed_tasks:
            for t in feed_tasks:
                t.execute()
        else:
            completed_feed = Task(
                description=f"Feeding {pet.name}",
                due_date=datetime.now(),
                priority=Priority.HIGH,
                type=TaskType.FEEDINGS,
                pet=pet,
                duration=15,
                is_completed=True,
            )
            pet.add_task(completed_feed)

    def play_with_pet(self, pet: Pet) -> None:
        play_tasks = [t for t in pet.tasks if t.type == TaskType.PLAY and not t.is_completed]
        if play_tasks:
            for t in play_tasks:
                t.execute()
        else:
            completed_play = Task(
                description=f"Play with {pet.name}",
                due_date=datetime.now(),
                priority=Priority.MEDIUM,
                type=TaskType.PLAY,
                pet=pet,
                duration=20,
                is_completed=True,
            )
            pet.add_task(completed_play)


@dataclass
class Scheduler:
    owner: Owner | None = None
    tasks: list[Task] = field(default_factory=list)

    def _resolve_tasks(self, owner: Owner | None = None) -> list[Task]:
        # Prioritize owner method for multi-pet tasks
        active_owner = owner or self.owner
        if active_owner is not None:
            return active_owner.get_all_tasks()
        return list(self.tasks)

    def schedule_task(self, task: Task) -> None:
        if task not in self.tasks:
            self.tasks.append(task)
        if task.pet and task not in task.pet.tasks:
            task.pet.add_task(task)

    def organize_tasks(
        self, tasks: list[Task] | None = None, owner: Owner | None = None
    ) -> list[Task]:
        task_list = tasks if tasks is not None else self._resolve_tasks(owner)
        priority_weights = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return sorted(
            task_list,
            key=lambda t: (
                priority_weights.get(t.priority, 1),
                t.due_date,
            ),
        )

    def see_todays_tasks(
        self, owner: Owner | None = None, target_date: datetime | None = None
    ) -> list[Task]:
        check_date = target_date.date() if target_date else datetime.now().date()
        tasks = self._resolve_tasks(owner)
        todays = [t for t in tasks if t.due_date.date() == check_date]
        return self.organize_tasks(todays)

    def alert_conflict(
        self,
        available_times: list[TimeSlot] | None = None,
        owner: Owner | None = None,
    ) -> list[tuple[Task, Task | TimeSlot]]:
        active_owner = owner or self.owner
        tasks = [t for t in self._resolve_tasks(owner) if not t.is_completed]
        conflicts: list[tuple[Task, Task | TimeSlot]] = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                t1, t2 = tasks[i], tasks[j]
                if t1.time_slot.overlaps(t2.time_slot):
                    conflicts.append((t1, t2))
        if active_owner is not None:
            for task in tasks:
                for blocked in active_owner.blocked_times:
                    if task.time_slot.overlaps(blocked):
                        conflicts.append((task, blocked))
        return conflicts

    def suggest_time_slot(
        self,
        duration_minutes: int,
        available_times: list[TimeSlot] | None = None,
        owner: Owner | None = None,
    ) -> TimeSlot | None:
        active_owner = owner or self.owner
        slots = available_times or (active_owner.available_times if active_owner else [])
        if not slots:
            return None

        tasks = [t for t in self._resolve_tasks(owner) if not t.is_completed]
        needed_duration = timedelta(minutes=duration_minutes)
        blocked_times = active_owner.blocked_times if active_owner else []

        for slot in slots:
            candidate_start = slot.start_time
            while candidate_start + needed_duration <= slot.end_time:
                candidate_slot = TimeSlot(candidate_start, candidate_start + needed_duration)
                overlap = False
                for task in tasks:
                    if candidate_slot.overlaps(task.time_slot):
                        overlap = True
                        candidate_start = task.end_time
                        break
                if overlap:
                    continue
                for blocked in blocked_times:
                    if candidate_slot.overlaps(blocked):
                        overlap = True
                        candidate_start = blocked.end_time
                        break
                if not overlap:
                    return candidate_slot
        return None
