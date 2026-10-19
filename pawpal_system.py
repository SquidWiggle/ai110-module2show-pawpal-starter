from dataclasses import dataclass, field
from datetime import datetime, timedelta, time as dt_time, date
from enum import Enum
from itertools import combinations


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
        if not self.end_time or not other.end_time:
            return False
        if not self.recurrence and not other.recurrence:
            return self.start_time < other.end_time and other.start_time < self.end_time

        def _intervals(slot: "TimeSlot", d: date, ignore_inception: bool = False) -> list[tuple[datetime, datetime]]:
            dur = slot.end_time - slot.start_time
            st = datetime.combine(d, slot.start_time.time())
            res = [(st, st + dur)]
            if slot.start_time.time() > slot.end_time.time() and slot.recurrence == Recurrence.DAILY:
                if ignore_inception or d > slot.start_time.date():
                    res.append((datetime.combine(d, dt_time.min), datetime.combine(d, slot.end_time.time())))
            return res

        if self.recurrence and other.recurrence:
            same_cycle = (
                (self.recurrence == other.recurrence == Recurrence.DAILY)
                or (self.recurrence == other.recurrence == Recurrence.WEEKLY and self.start_time.weekday() == other.start_time.weekday())
                or (self.recurrence == other.recurrence == Recurrence.MONTHLY and self.start_time.day == other.start_time.day)
                or self.recurrence == Recurrence.DAILY
                or other.recurrence == Recurrence.DAILY
            )
            if not same_cycle:
                return False
            ref = date(2000, 1, 2)
            return any(s1 < e2 and s2 < e1 for s1, e1 in _intervals(self, ref, ignore_inception=True) for s2, e2 in _intervals(other, ref, ignore_inception=True))

        rec, fix = (self, other) if self.recurrence else (other, self)
        if fix.end_time.date() < rec.start_time.date():
            return False

        def _matches(d: date) -> bool:
            return (
                rec.recurrence == Recurrence.DAILY
                or (rec.recurrence == Recurrence.WEEKLY and d.weekday() == rec.start_time.weekday())
                or (rec.recurrence == Recurrence.MONTHLY and d.day == rec.start_time.day)
            )

        d_curr = fix.start_time.date() - timedelta(days=1)
        d_end = fix.end_time.date()
        while d_curr <= d_end:
            if d_curr >= rec.start_time.date() and _matches(d_curr):
                for s, e in _intervals(rec, d_curr):
                    if s < fix.end_time and fix.start_time < e:
                        return True
            d_curr += timedelta(days=1)
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


def _parse_time(val: datetime | str | date | dt_time | None, base: date | None = None) -> datetime:
    if val is None:
        return datetime.now()
    if isinstance(val, datetime):
        return val
    base_date = base or date.today()
    if isinstance(val, str):
        parts = [int(p) for p in val.split(":")]
        return datetime.combine(base_date, dt_time(parts[0], parts[1], parts[2] if len(parts) > 2 else 0))
    if isinstance(val, dt_time):
        return datetime.combine(base_date, val)
    if isinstance(val, date):
        return datetime.combine(val, dt_time.min)
    return val


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
        due_date: datetime | str | date | None = None,
        priority: Priority | str = Priority.MEDIUM,
        type: TaskType | str = TaskType.WALKS,
        pet: Pet | None = None,
        duration: int = 30,
        recurrence: Recurrence | str | None = None,
        is_completed: bool = False,
        time: datetime | str | None = None,
        frequency: Recurrence | str | None = None,
        completion_status: bool | None = None,
    ):
        raw_val = due_date if due_date is not None else time
        self.due_date = _parse_time(raw_val)
        self.type = TaskType(type.upper()) if isinstance(type, str) else type
        self.description = description or (self.type.value if hasattr(self.type, "value") else str(self.type))
        self.priority = Priority(priority.upper()) if isinstance(priority, str) else priority
        self.pet = pet
        self.duration = duration
        rec = recurrence if recurrence is not None else frequency
        self.recurrence = Recurrence(rec.upper()) if isinstance(rec, str) else rec
        self.is_completed = completion_status if completion_status is not None else is_completed

    @property
    def time(self) -> datetime:
        return self.due_date

    @time.setter
    def time(self, val: datetime | str | dt_time | date) -> None:
        self.due_date = _parse_time(val, self.due_date.date() if isinstance(self.due_date, datetime) else None)

    @property
    def frequency(self) -> Recurrence | None:
        return self.recurrence

    @frequency.setter
    def frequency(self, val: Recurrence | str | None) -> None:
        self.recurrence = Recurrence(val.upper()) if isinstance(val, str) else val

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
        return TimeSlot(
            start_time=self.due_date,
            end_time=self.end_time,
            recurrence=self.recurrence,
        )

    def execute(self) -> "Task | None":
        return self.mark_complete()

    def mark_complete(self) -> "Task | None":
        if self.is_completed:
            return None
        self.is_completed = True

        delta = {
            Recurrence.DAILY: timedelta(days=1),
            Recurrence.WEEKLY: timedelta(weeks=1),
            Recurrence.MONTHLY: timedelta(days=30),
        }.get(self.recurrence)

        if delta is not None:
            next_task = Task(
                description=self.description,
                due_date=self.due_date + delta,
                priority=self.priority,
                type=self.type,
                pet=self.pet,
                duration=self.duration,
                recurrence=self.recurrence,
                is_completed=False,
            )
            if self.pet:
                self.pet.add_task(next_task)
            return next_task
        return None


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
                    if match and curr >= b.start_time.date():
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
        tasks: list[Task] = []
        for t in [task for pet in self.pets for task in pet.tasks] + (self.scheduler.tasks if self.scheduler else []):
            if t not in tasks:
                tasks.append(t)
        return tasks

    def schedule_task(self, arg1: "Scheduler | Task", arg2: Task | None = None) -> None:
        target_scheduler, task = (self.scheduler or Scheduler(owner=self), arg1) if isinstance(arg1, Task) else (arg1, arg2)
        if not task:
            return
        if not self.scheduler:
            self.scheduler = target_scheduler
        if task.pet:
            if task.pet not in self.pets:
                self.add_pet(task.pet)
            task.pet.add_task(task)
        target_scheduler.schedule_task(task)


def _ceil_15_mins(dt: datetime) -> datetime:
    discard = timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)
    if discard.total_seconds() == 0:
        return dt
    return dt - discard + timedelta(minutes=15)


@dataclass
class Scheduler:
    owner: Owner | None = None
    tasks: list[Task] = field(default_factory=list)

    def _resolve_tasks(self, owner: Owner | None = None) -> list[Task]:
        active_owner = owner or self.owner
        candidates = (active_owner.get_all_tasks() if active_owner else []) + self.tasks
        resolved: list[Task] = []
        for t in candidates:
            if t not in resolved:
                resolved.append(t)
        return resolved

    def get_all_tasks(
        self, upcoming_only: bool = False, owner: Owner | None = None
    ) -> list[Task]:
        tasks = self._resolve_tasks(owner)
        if upcoming_only:
            now = datetime.now()
            tasks = [t for t in tasks if t.end_time >= now]
        return tasks

    def schedule_task(self, task: Task) -> None:
        if task not in self.tasks:
            self.tasks.append(task)
        if task.pet and task not in task.pet.tasks:
            task.pet.add_task(task)

    def complete_task(self, task: Task) -> Task | None:
        next_task = task.mark_complete()
        if next_task:
            if next_task not in self.tasks:
                self.tasks.append(next_task)
            if self.owner and next_task.pet and next_task.pet not in self.owner.pets:
                self.owner.add_pet(next_task.pet)
        return next_task

    def organize_tasks(
        self,
        tasks: list[Task] | None = None,
        owner: Owner | None = None,
        by_priority: bool = False,
    ) -> list[Task]:
        task_list = tasks if tasks is not None else self._resolve_tasks(owner)
        priority_weights = {Priority.HIGH: 0,
                            Priority.MEDIUM: 1, Priority.LOW: 2}
        if by_priority:
            return sorted(
                task_list,
                key=lambda t: (
                    priority_weights.get(t.priority, 1),
                    t.due_date,
                ),
            )
        return sorted(
            task_list,
            key=lambda t: (
                t.due_date,
                priority_weights.get(t.priority, 1),
            ),
        )

    def sort_by_priority(
        self, tasks: list[Task] | None = None, owner: Owner | None = None
    ) -> list[Task]:
        return self.organize_tasks(tasks=tasks, owner=owner, by_priority=True)

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

        return sorted(task_list, key=lambda t: t.due_date)

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
        for t1, t2 in combinations(tasks, 2):
            if t1.time_slot.overlaps(t2.time_slot):
                conflicts.append((t1, t2))
        if active_owner is not None:
            for task in tasks:
                for blocked in active_owner.blocked_times:
                    if task.time_slot.overlaps(blocked):
                        conflicts.append((task, blocked))
        return conflicts

    def get_conflict_warnings(
        self,
        owner: Owner | None = None,
        conflicts: list[tuple[Task, Task | TimeSlot]] | None = None,
    ) -> list[str]:
        if conflicts is None:
            conflicts = self.alert_conflict(owner=owner)
        warnings: list[str] = []

        for item1, item2 in conflicts:
            if isinstance(item2, Task):
                t1, t2 = item1, item2
                t1_pet = t1.pet.name if t1.pet else "Unassigned"
                t2_pet = t2.pet.name if t2.pet else "Unassigned"
                time_info = f"{t1.due_date.strftime('%H:%M')} - {t1.end_time.strftime('%H:%M')}"
                if t1.pet and t2.pet and t1.pet == t2.pet:
                    warnings.append(
                        f"⚠️ [Same-Pet Conflict] {t1_pet} is double-booked: "
                        f"'{t1.description}' and '{t2.description}' overlap around {time_info}."
                    )
                else:
                    warnings.append(
                        f"⚠️ [Concurrent Care Conflict] Overlapping pet tasks: "
                        f"{t1_pet} ('{t1.description}') and {t2_pet} ('{t2.description}') "
                        f"overlap around {time_info}."
                    )
            elif isinstance(item2, TimeSlot):
                task, blocked = item1, item2
                pet_name = task.pet.name if task.pet else "Task"
                block_desc = blocked.description or "Blocked Time"
                warnings.append(
                    f"⚠️ [Blocked Time Collision] {pet_name} task '{task.description}' "
                    f"collides with owner's {block_desc} schedule."
                )

        return warnings

    def suggest_time_slot(
        self,
        duration_minutes: int,
        available_times: list[TimeSlot] | None = None,
        owner: Owner | None = None,
        search_start: datetime | None = None,
    ) -> TimeSlot | None:
        active_owner = owner or self.owner
        default_computed = False
        slots = available_times or (
            active_owner.available_times if active_owner and active_owner.available_times else [])
        if not slots and active_owner and active_owner.blocked_times:
            default_computed = True
            ref_now = search_start or datetime.now()
            day_start = datetime(ref_now.year, ref_now.month, ref_now.day, 0, 0)
            day_end = day_start + timedelta(days=1)
            slots = active_owner.get_available_times(day_start, day_end)
        if not slots:
            return None

        tasks = [t for t in self._resolve_tasks(owner) if not t.is_completed]
        needed_duration = timedelta(minutes=duration_minutes)
        blocked_times = active_owner.blocked_times if active_owner else []

        min_start = None
        if search_start is not None:
            min_start = _ceil_15_mins(search_start)
        elif default_computed:
            min_start = _ceil_15_mins(datetime.now())

        for slot in slots:
            candidate_start = slot.start_time
            if min_start and candidate_start < min_start:
                candidate_start = min_start
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
