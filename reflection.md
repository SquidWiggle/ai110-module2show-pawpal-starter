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
  - Yes.
- If yes, describe at least one change and why you made it.
  - I've initially put see_todays_task() and schedule_task() under Owner class, and used a map as the type of Owner's available time slot. I've also put eat() as Pet's method. AI suggested to single out Owner and Scheduler's responsibilities, add datetime type for Scheduler to check time conflict later, and remove eat() since it is a duplicate of Owner's feed() method. I agreed.
  - I checked if using the same TaskType Enum in Pet's required_care list made sense, and AI answered it eliminates string mismatching, enables type checking, and most importantly restricts pet care requirements to defined single source of truth, so it is a good move.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - I was presented with changes to the conflict detection algorithm in Scheduler.alert_conflict and Scheduler.get_conflict_warnings by AI. I can choose either improving it with itertools for readability, or using High-Performance Sweep-Line (O(N log N)) to speed it up. I chosed the itertools version for readability.
- Why is that tradeoff reasonable for this scenario?
  -  Yes because when N<20, which is the case here where number of task is for one pet owner, the difference is negligible.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  - I used AI to brainstorm, improve, and enrich my system design.
  - AI has helped review my first round of implementation and catch bugs. 
  - During review, I asked AI to generate default time block for Owner's "slepp" time and "work" time so the app become actually useful to the pet owners. AI suggested implementation plan, and helped me evaluate different way of implementations.
- What kinds of prompts or questions were most helpful?
  - Asking AI to review existing code to catch bugs. Describe use case as specifically as possible.
  - Evaluate alternative implementations and checking if the implementation is as minimal as possible.
**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  - I questioned the implementation plan AI suggested and asked to use the same underlying implementation for the feature to block out time periods that are slee/work vs. time periods for Task scheduling. However, after advising subagent on a higher tier model, I agreed because Task have extra fields (is_complete, priority). They will pollute the class if using the same imepleentation. Instead, I suggested to not expose Scheduler class to the user, which was overlooked by the AI reviews.
- How did you evaluate or verify what the AI suggested?
  - Run the app manually.
  - Design test cases and run them in UI.

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
  - AI is good at pulling in advisor opinions when I have questions.
  - Planing, review, and then executing gives better result than executing immediately.