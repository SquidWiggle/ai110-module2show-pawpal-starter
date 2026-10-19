# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

A user of PawPal+ should be able to
1. add a pet
2. feed a pet
3. see today's task
4. schedule a walk

- Briefly describe your initial UML design.

Owner:
  - attributes:
    - name: str
    - pets: []Pet
    - available_time: TimeSlot
  - methods:
    - schedule_task(task_type)
    - add_pet
    - feed_pet
    - play_with_pet

Pet:
  - attributes:
    - name
    - species
    - breed
    - required_care: [food, walk, play_time, grooming]


Task:
  - attributes:
    - due_date: datetime
    - priority: Enum (high, medium, low)
    - type: Enum (feedings, walks, medications, vet appointment, play, grooming)
    - pet: Pet
    - duration: int (minutes)
    - recurrence: Enum (daily, weekly, monthly)
  - methods:
    - execute

Scheduler:
  - attrubutes:
    - tasks: Task[]
  - methods:
    - schedule a task
    - see_todays_task
    - alert about a conflict
    - suggest time slot


- What classes did you include, and what responsibilities did you assign to each?
  - Owner: The user of the app who can have a existing schedule. The owner is responsible for scheduling tasks to take care of their pets. An owner can have multiple pets.
  - Pet: A pet that can be adopted by the owner. It is responsible for nothing much other than eat and play. A pet come with the care it needs. A pet can need only food, walk, or grooming, or it can need medication, play_time, frequent vet_appointments.
  - Task: Task object holds information about the task - which pet the task applies to, duration of the task, priority of the task.
  - Scheduler: A scheduler keeps track of the tasks an owner has scheduled on their calendar.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
