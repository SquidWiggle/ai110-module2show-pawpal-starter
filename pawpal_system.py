from dataclasses import dataclass, field
from datetime import datetime, timedelta, time, date
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
    end_time: datetime | None = None
    duration: int | None = None
    recurrence: Recurrence | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if self.end_time is None and self.duration is not None:
            self.end_time = self.start_time + timedelta(minutes=self.duration)
        elif self.duration is None and self.end_time is not None:
            self.duration = int(
                (self.end_time - self.start_time).total_seconds() // 60)
        elif self.end_time is None and self.duration is None:
            self.end_time = self.start_time
            self.duration = 0

    def overlaps(self, other: "TimeSlot") -> bool:
        if self.end_time is None or other.end_time is None:
            return False
        if self.start_time < other.end_time and other.start_time < self.end_time:
            return True
        if self.recurrence == Recurrence.DAILY or other.recurrence == Recurrence.DAILY:
            s1, e1 = self.start_time.time(), self.end_time.time()
            s2, e2 = other.start_time.time(), other.end_time.time()

            def _daily_segments(s: time, e: time) -> list[tuple[time, time]]:
                return [(s, time.max), (time.min, e)] if s > e else [(s, e)]

            for a_s, a_e in _daily_segments(s1, e1):
                for b_s, b_e in _daily_segments(s2, e2):
                    if a_s < b_e and b_s < a_e:
                        return True
        return False


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
            self.description = self.type.value if hasattr(
                self.type, "value") else str(self.type)

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

    def mark_complete(self) -> None:
        self.is_completed = True


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)
    available_times: list[TimeSlot] = field(default_factory=list)
    blocked_times: list[TimeSlot] = field(default_factory=list)
    scheduler: "Scheduler | None" = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.scheduler is None:
            self.scheduler = Scheduler(owner=self)
        elif self.scheduler.owner is None:
            self.scheduler.owner = self

    def add_pet(self, pet: Pet) -> None:
        if pet not in self.pets:
            self.pets.append(pet)

    def block_time(
        self,
        start_time: datetime,
        duration: int | None = None,
        end_time: datetime | None = None,
        recurrence: Recurrence | None = None,
        description: str = "",
    ) -> TimeSlot:
        slot = TimeSlot(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            recurrence=recurrence,
            description=description,
        )
        self.blocked_times.append(slot)
        return slot

    def get_available_times(self, start: datetime, end: datetime) -> list[TimeSlot]:
        free_intervals = [(start, end)]
        relevant_blocks: list[tuple[datetime, datetime]] = []
        for b in self.blocked_times:
            if b.end_time is None:
                continue
            if b.recurrence in (Recurrence.DAILY, Recurrence.WEEKLY, Recurrence.MONTHLY):
                block_dur = b.duration or int(
                    (b.end_time - b.start_time).total_seconds() // 60)
                curr = start.date() - timedelta(days=1)
                while curr <= end.date():
                    match = (
                        b.recurrence == Recurrence.DAILY
                        or (b.recurrence == Recurrence.WEEKLY and curr.weekday() == b.start_time.weekday())
                        or (b.recurrence == Recurrence.MONTHLY and curr.day == b.start_time.day)
                    )
                    if match:
                        b_start = datetime.combine(curr, b.start_time.time())
                        b_end = b_start + timedelta(minutes=block_dur)
                        if b_start < end and b_end > start:
                            relevant_blocks.append(
                                (max(start, b_start), min(end, b_end)))
                    curr += timedelta(days=1)
            else:
                if b.start_time < end and b.end_time > start:
                    relevant_blocks.append(
                        (max(start, b.start_time), min(end, b.end_time)))

        for b_start, b_end in sorted(relevant_blocks, key=lambda x: x[0]):
            new_free = []
            for f_start, f_end in free_intervals:
                if b_end <= f_start or b_start >= f_end:
                    new_free.append((f_start, f_end))
                else:
                    if f_start < b_start:
                        new_free.append((f_start, b_start))
                    if b_end < f_end:
                        new_free.append((b_end, f_end))
            free_intervals = new_free

        return [TimeSlot(s, e) for s, e in free_intervals]

    def get_all_tasks(self) -> list[Task]:
        # Aggregate tasks across every pet
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def schedule_task(self, arg1: "Scheduler | Task", arg2: Task | None = None) -> None:
        if isinstance(arg1, Task):
            task = arg1
            target_scheduler = arg2 or self.scheduler or Scheduler(owner=self)
        else:
            target_scheduler = arg1
            task = arg2

        if task is None:
            return
        if task.pet and task.pet in self.pets and task not in task.pet.tasks:
            task.pet.add_task(task)
        target_scheduler.schedule_task(task)

    def feed_pet(self, pet: Pet) -> None:
        feed_tasks = [t for t in pet.tasks if t.type ==
                      TaskType.FEEDINGS and not t.is_completed]
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
        play_tasks = [t for t in pet.tasks if t.type ==
                      TaskType.PLAY and not t.is_completed]
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
        priority_weights = {Priority.HIGH: 0,
                            Priority.MEDIUM: 1, Priority.LOW: 2}
        return sorted(
            task_list,
            key=lambda t: (
                t.due_date,
                priority_weights.get(t.priority, 1),
            ),
        )

    def sort_by_time(
        self,
        tasks: list[Task] | None = None,
        owner: Owner | None = None,
        pet: Pet | str | None = None,
        is_completed: bool | None = None,
        completion_status: bool | None = None,
    ) -> list[Task]:
        task_list = list(tasks) if tasks is not None else self._resolve_tasks(owner)

        if pet is not None:
            pet_name = pet.name if hasattr(pet, "name") else str(pet)
            task_list = [t for t in task_list if t.pet and t.pet.name.lower() == pet_name.lower()]

        target_status = completion_status if completion_status is not None else is_completed
        if target_status is not None:
            task_list = [t for t in task_list if t.is_completed == target_status]

        def _sort_key(t: Task):
            val = t.time
            if isinstance(val, str):
                return [int(p) for p in val.split(":")]
            return val

        return sorted(task_list, key=_sort_key)


    def see_todays_tasks(
        self, owner: Owner | None = None, target_date: datetime | date | None = None
    ) -> list[Task]:
        if target_date is None:
            check_date = datetime.now().date()
        elif isinstance(target_date, datetime):
            check_date = target_date.date()
        elif isinstance(target_date, date):
            check_date = target_date
        elif hasattr(target_date, "date"):
            check_date = target_date.date()
        else:
            check_date = target_date
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
        slots = available_times or (
            active_owner.available_times if active_owner and active_owner.available_times else [])
        if not slots and active_owner and active_owner.blocked_times:
            now = datetime.now()
            day_start = datetime(now.year, now.month, now.day, 0, 0)
            day_end = day_start + timedelta(days=1)
            slots = active_owner.get_available_times(day_start, day_end)
        if not slots:
            return None

        tasks = [t for t in self._resolve_tasks(owner) if not t.is_completed]
        needed_duration = timedelta(minutes=duration_minutes)
        blocked_times = active_owner.blocked_times if active_owner else []

        for slot in slots:
            candidate_start = slot.start_time
            while candidate_start + needed_duration <= slot.end_time:
                candidate_slot = TimeSlot(
                    candidate_start, candidate_start + needed_duration)
                overlap = False
                for task in tasks:
                    if candidate_slot.overlaps(task.time_slot):
                        overlap = True
                        candidate_start = max(
                            task.end_time, candidate_start + timedelta(minutes=15))
                        break
                if overlap:
                    continue
                for blocked in blocked_times:
                    if candidate_slot.overlaps(blocked):
                        overlap = True
                        prev_start = candidate_start
                        if blocked.recurrence == Recurrence.DAILY and blocked.end_time:
                            proj_end = datetime.combine(
                                candidate_start.date(), blocked.end_time.time())
                            if proj_end <= candidate_start:
                                proj_end += timedelta(days=1)
                            candidate_start = proj_end
                        else:
                            candidate_start = blocked.end_time or (
                                candidate_start + timedelta(minutes=15))
                        if candidate_start <= prev_start:
                            candidate_start = prev_start + \
                                timedelta(minutes=15)
                        break
                if not overlap:
                    return candidate_slot
        return None
