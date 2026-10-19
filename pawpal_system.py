from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    required_care: list[TaskType] = field(default_factory=list)


@dataclass
class Task:
    due_date: datetime
    priority: Priority
    type: TaskType
    pet: Pet
    duration: int
    recurrence: Recurrence | None = None

    def execute(self) -> None:
        pass


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)
    available_time: TimeSlot | None = None

    def schedule_task(self, task_type: TaskType) -> None:
        pass

    def add_pet(self, pet: Pet) -> None:
        pass

    def feed_pet(self, pet: Pet) -> None:
        pass

    def play_with_pet(self, pet: Pet) -> None:
        pass


@dataclass
class Scheduler:
    tasks: list[Task] = field(default_factory=list)

    def schedule_task(self, task: Task) -> None:
        pass

    def see_todays_tasks(self) -> list[Task]:
        pass

    def alert_conflict(self) -> None:
        pass

    def suggest_time_slot(self) -> TimeSlot | None:
        pass

