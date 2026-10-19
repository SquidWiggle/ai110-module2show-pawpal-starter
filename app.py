import streamlit as st
from datetime import datetime, date, time, timedelta
from pawpal_system import (
    Owner,
    Pet,
    Task,
    TaskType,
    Priority,
    Recurrence,
    TimeSlot,
)

st.set_page_config(page_title="PawPal+ Care Planner", page_icon="🐾", layout="wide")

# Session Vault Initialization
if "owner" not in st.session_state:
    owner = Owner(name="Jordan")
    today_base = date.today()
    sleep_start = datetime.combine(today_base, time(0, 0))
    owner.block_time(
        start_time=sleep_start,
        duration=480,
        recurrence=Recurrence.DAILY,
        description="Sleep",
    )
    work_start = datetime.combine(today_base, time(9, 0))
    owner.block_time(
        start_time=work_start,
        duration=480,
        recurrence=Recurrence.DAILY,
        description="Work",
    )
    owner.add_pet(Pet(name="Mochi", species="Dog", breed="Shiba Inu"))
    st.session_state["owner"] = owner

owner: Owner = st.session_state["owner"]

# ----------------- SIDEBAR -----------------
st.sidebar.title("🐾 PawPal+ Controls")

# Owner Profile & Blocked Times
st.sidebar.header("Owner Profile & Blocked Times")
st.sidebar.markdown(f"**Owner:** {owner.name}")

st.sidebar.markdown("**Blocked Times:**")
if owner.blocked_times:
    for b in owner.blocked_times:
        rec_label = f" ({b.recurrence.value})" if b.recurrence else ""
        end_str = b.end_time.strftime("%H:%M") if b.end_time else "N/A"
        time_str = f"{b.start_time.strftime('%H:%M')} - {end_str}"
        st.sidebar.markdown(f"- **{b.description or 'Blocked'}**: `{time_str}`{rec_label}")
else:
    st.sidebar.caption("No blocked times configured.")

with st.sidebar.expander("Add Blocked Time", expanded=False):
    with st.form("block_time_form"):
        block_desc = st.text_input("Description", value="Break")
        block_date = st.date_input("Start Date", value=date.today(), key="block_date_input")
        block_time = st.time_input("Start Time", value=time(12, 0), key="block_time_input")
        block_dur = st.number_input("Duration (minutes)", min_value=5, max_value=1440, value=60, step=5)
        block_rec = st.selectbox("Recurrence", ["None", "DAILY", "WEEKLY", "MONTHLY"], key="block_rec_select")
        block_submitted = st.form_submit_button("Add Blocked Time")
        if block_submitted:
            rec_enum = Recurrence(block_rec) if block_rec != "None" else None
            start_dt = datetime.combine(block_date, block_time)
            owner.block_time(
                start_time=start_dt,
                duration=int(block_dur),
                recurrence=rec_enum,
                description=block_desc,
            )
            st.success("Blocked time added!")
            st.rerun()

# Manage Pets
st.sidebar.header("Manage Pets")
st.sidebar.markdown("**Registered Pets:**")
if owner.pets:
    for p in owner.pets:
        st.sidebar.markdown(f"- 🐶 **{p.name}** ({p.species} • {p.breed})")
else:
    st.sidebar.caption("No pets registered.")

with st.sidebar.expander("Add New Pet", expanded=False):
    with st.form("add_pet_form"):
        new_pet_name = st.text_input("Pet Name")
        new_pet_species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Other"])
        new_pet_breed = st.text_input("Breed", value="Mixed")
        add_pet_submitted = st.form_submit_button("Add Pet")
        if add_pet_submitted:
            if new_pet_name.strip():
                owner.add_pet(
                    Pet(
                        name=new_pet_name.strip(),
                        species=new_pet_species,
                        breed=new_pet_breed.strip(),
                    )
                )
                st.success(f"Added pet {new_pet_name.strip()}!")
                st.rerun()
            else:
                st.error("Pet name cannot be empty.")

# Schedule Task Form
st.sidebar.header("Schedule Task")
if not owner.pets:
    st.sidebar.warning("Please add at least one pet before scheduling tasks.")
else:
    pet_dict = {f"{p.name} ({p.species})": p for p in owner.pets}
    selected_pet_label = st.sidebar.selectbox("Select Pet", list(pet_dict.keys()))
    selected_pet = pet_dict.get(selected_pet_label, owner.pets[0])

    task_desc = st.sidebar.text_input("Task Description", value="Morning Walk")
    task_type = st.sidebar.selectbox("Task Type", list(TaskType), format_func=lambda t: t.value)
    task_priority = st.sidebar.selectbox(
        "Priority",
        [Priority.HIGH, Priority.MEDIUM, Priority.LOW],
        format_func=lambda p: p.value,
        index=0,
    )
    task_date = st.sidebar.date_input("Due Date", value=date.today(), key="task_date_picker")
    task_time = st.sidebar.time_input("Due Time", value=time(8, 30), key="task_time_picker")
    task_duration = st.sidebar.number_input(
        "Duration (minutes)",
        min_value=5,
        max_value=240,
        value=30,
        step=5,
        key="task_duration_picker",
    )
    task_rec_choice = st.sidebar.selectbox(
        "Recurrence",
        ["None", "DAILY", "WEEKLY", "MONTHLY"],
        key="task_rec_picker",
    )

    if st.sidebar.button("Schedule Task"):
        due_datetime = datetime.combine(task_date, task_time)
        task_rec = Recurrence(task_rec_choice) if task_rec_choice != "None" else None
        task = Task(
            description=task_desc.strip() or task_type.value,
            due_date=due_datetime,
            priority=task_priority,
            type=task_type,
            pet=selected_pet,
            duration=int(task_duration),
            recurrence=task_rec,
        )
        owner.schedule_task(task)
        st.sidebar.success(f"Scheduled task: {task.description}!")
        st.rerun()

# ----------------- MAIN PANEL -----------------
st.title("🐾 PawPal+ Pet Care Planner")

# Conflict Analysis & Notifications (Elevated at Top)
conflict_warnings = owner.scheduler.get_conflict_warnings()
conflicts = owner.scheduler.alert_conflict()
conflicting_task_ids = set()
for c1, c2 in conflicts:
    conflicting_task_ids.add(id(c1))
    if isinstance(c2, Task):
        conflicting_task_ids.add(id(c2))

if conflict_warnings:
    with st.expander(f"⚠️ Schedule Conflicts Detected ({len(conflict_warnings)})", expanded=True):
        for w in conflict_warnings:
            if "[Same-Pet Conflict]" in w or "[Blocked Time Collision]" in w:
                st.error(w)
            else:
                st.warning(w)
else:
    st.success("✅ All schedules clear — no task or blocked-time collisions detected.")

st.divider()

# Schedule Controls & Filtering Toolbar
st.header("📅 Pet Care Schedule")

col_scope, col_date, col_pet, col_status, col_sort = st.columns([2, 2, 2, 2, 2])

with col_scope:
    view_scope = st.selectbox("View Scope", ["Target Date", "All Upcoming"], key="view_scope_select")

with col_date:
    selected_date = st.date_input(
        "Target Date",
        value=date.today(),
        key="target_date_picker",
        disabled=(view_scope == "All Upcoming"),
    )

with col_pet:
    pet_options = ["All Pets"] + [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("Filter Pet", pet_options, key="filter_pet_select")

with col_status:
    selected_status = st.selectbox("Filter Status", ["All", "Pending Only", "Completed Only"], key="filter_status_select")

with col_sort:
    selected_sort = st.selectbox("Sort By", ["Time (Chronological)", "Priority (High → Low)"], key="sort_by_select")

# Resolve tasks using Scheduler methods
if view_scope == "Target Date":
    base_tasks = owner.scheduler.see_todays_tasks(target_date=selected_date)
else:
    base_tasks = owner.scheduler._resolve_tasks()

pet_filter = None if selected_pet_name == "All Pets" else selected_pet_name
status_filter = None
if selected_status == "Pending Only":
    status_filter = False
elif selected_status == "Completed Only":
    status_filter = True

# Leverage Scheduler.sort_by_time and Scheduler.organize_tasks
filtered_time_tasks = owner.scheduler.sort_by_time(
    tasks=base_tasks,
    pet=pet_filter,
    completion_status=status_filter,
)

if selected_sort == "Priority (High → Low)":
    tasks = owner.scheduler.organize_tasks(tasks=filtered_time_tasks)
else:
    tasks = filtered_time_tasks

# Render Tasks: Tabular & Card Views
tab_cards, tab_table = st.tabs(["📇 Task Cards", "📊 Data Table"])

with tab_table:
    if not tasks:
        st.info("No tasks to display matching the current filters.")
    else:
        table_rows = []
        for t in tasks:
            table_rows.append(
                {
                    "Time": f"{t.due_date.strftime('%Y-%m-%d %H:%M')} - {t.end_time.strftime('%H:%M')}",
                    "Pet": t.pet.name if t.pet else "Unassigned",
                    "Task": t.description,
                    "Type": t.type.value,
                    "Priority": t.priority.value,
                    "Recurrence": t.recurrence.value if t.recurrence else "None",
                    "Status": "✅ Completed" if t.is_completed else "⏳ Pending",
                    "Conflict": "⚠️ Yes" if id(t) in conflicting_task_ids else "None",
                }
            )
        st.table(table_rows)

with tab_cards:
    if not tasks:
        st.info("No tasks to display matching the current filters.")
    else:
        for idx, t in enumerate(tasks):
            is_conflict = id(t) in conflicting_task_ids
            due_str = (
                t.due_date.strftime("%Y-%m-%d %H:%M")
                if view_scope == "All Upcoming"
                else t.due_date.strftime("%H:%M")
            )
            end_str = t.end_time.strftime("%H:%M")
            pet_name = t.pet.name if t.pet else "Unassigned"
            rec_badge = f" • 🔁 {t.recurrence.value}" if t.recurrence else ""
            conflict_badge = " • ⚠️ **CONFLICT**" if is_conflict else ""

            with st.container(border=True):
                col_time, col_details, col_status, col_action = st.columns([2, 4, 2, 2])
                with col_time:
                    st.markdown(f"**⏰ {due_str} - {end_str}**")
                    st.caption(f"🐾 **{pet_name}**{rec_badge}{conflict_badge}")
                with col_details:
                    st.markdown(f"**{t.description}**")
                    st.caption(
                        f"Type: `{t.type.value}` | Priority: `{t.priority.value}` | Duration: {t.duration} mins"
                    )
                with col_status:
                    if t.is_completed:
                        st.success("✅ Completed")
                    elif is_conflict:
                        st.error("⚠️ Conflict")
                    else:
                        st.warning("⏳ Pending")
                with col_action:
                    if not t.is_completed:
                        if st.button("Mark Complete", key=f"complete_{idx}_{t.due_date.timestamp()}_{id(t)}"):
                            owner.scheduler.complete_task(t)
                            st.rerun()

st.divider()

# Open Time Slot Finder
st.header("🔍 Open Time Slot Finder")
st.markdown("Find an available opening in the owner's schedule that does not overlap with tasks or blocked times.")
finder_col1, finder_col2 = st.columns([2, 1])
with finder_col1:
    slot_duration = st.number_input(
        "Required duration (minutes)",
        min_value=5,
        max_value=240,
        value=30,
        step=5,
        key="open_slot_duration_input",
    )
with finder_col2:
    st.write("")
    st.write("")
    find_button = st.button("Find Open Slot")

if find_button:
    open_slot = owner.scheduler.suggest_time_slot(duration_minutes=int(slot_duration))
    if open_slot:
        start_fmt = open_slot.start_time.strftime("%Y-%m-%d %H:%M")
        end_fmt = open_slot.end_time.strftime("%H:%M")
        st.success(f"✅ Available slot found: **{start_fmt} - {end_fmt}** ({open_slot.duration} minutes)")
    else:
        st.warning("No available time slot found for the requested duration.")
