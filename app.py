import logging
import streamlit as st
from datetime import date, datetime, time
from dotenv import load_dotenv

from ai_explainer import GeminiPlanExplainer, explain_plan_with_fallback
from pawpal_system import Owner, Pet, Scheduler, Task

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if "owner" not in st.session_state or not isinstance(st.session_state.owner, Owner):
    st.session_state.owner = Owner(owner_id=1, name=owner_name, available_minutes_per_day=180)

owner: Owner = st.session_state.owner
owner.name = owner_name

if "scheduler" not in st.session_state or not isinstance(st.session_state.scheduler, Scheduler):
    st.session_state.scheduler = Scheduler(owner)

scheduler: Scheduler = st.session_state.scheduler
scheduler.owner = owner

if "ai_explainer" not in st.session_state:
    try:
        st.session_state.ai_explainer = GeminiPlanExplainer()
        st.session_state.ai_explainer_error = ""
        logger.info("Streamlit AI explainer initialized")
    except RuntimeError as error:
        st.session_state.ai_explainer = None
        st.session_state.ai_explainer_error = str(error)
        logger.warning("Streamlit running without AI explainer: %s", error)

if "pet_id_counter" not in st.session_state:
    st.session_state.pet_id_counter = 1

if "task_id_counter" not in st.session_state:
    st.session_state.task_id_counter = 1

if st.button("Add pet"):
    new_pet = Pet(
        pet_id=st.session_state.pet_id_counter,
        name=pet_name,
        species=species,
        owner_id=owner.owner_id,
    )
    owner.add_pet(new_pet)
    st.session_state.pet_id_counter += 1
    st.success(f"Added pet: {new_pet.name}")

if owner.pets:
    st.write("Current pets:")
    st.table(
        [
            {"pet_id": pet.pet_id, "name": pet.name, "species": pet.species}
            for pet in owner.pets
        ]
    )
else:
    st.info("No pets added yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add tasks to a pet using your backend methods.")

if owner.pets:
    pet_options = {f"{pet.name} (#{pet.pet_id})": pet.pet_id for pet in owner.pets}
    selected_pet_label = st.selectbox("Pet for this task", list(pet_options.keys()))
    selected_pet_id = pet_options[selected_pet_label]
else:
    selected_pet_id = None
    st.warning("Add a pet before creating tasks.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    task_date = st.date_input("Task date", value=date.today())
with col5:
    task_time = st.time_input("Task time", value=time(8, 0))

frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=0)

priority_map = {"low": 1, "medium": 2, "high": 3}

if st.button("Add task"):
    if selected_pet_id is None:
        st.error("Please add a pet first.")
    else:
        selected_pet = owner.get_pet(selected_pet_id)
        scheduled_for = datetime.combine(task_date, task_time)
        new_task = Task(
            task_id=st.session_state.task_id_counter,
            pet_id=selected_pet_id,
            description=task_title,
            scheduled_for=scheduled_for,
            frequency=frequency,
            duration_minutes=int(duration),
            priority=priority_map[priority],
        )
        selected_pet.add_task(new_task)
        st.session_state.task_id_counter += 1
        st.success(f"Added task: {new_task.description}")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "task_id": task.task_id,
                "pet_id": task.pet_id,
                "description": task.description,
                "time": task.scheduled_for.strftime("%Y-%m-%d %I:%M %p") if task.scheduled_for else "",
                "frequency": task.frequency,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
                "completed": task.is_completed,
            }
            for task in all_tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate today's schedule using your Scheduler class.")

plan_date = st.date_input("Schedule date", value=date.today(), key="schedule_date")

if st.button("Generate schedule"):
    plan = scheduler.generate_daily_plan(plan_date)
    if not plan:
        st.info("No tasks scheduled for that date.")
    else:
        pet_names = {pet.pet_id: pet.name for pet in owner.pets}
        st.write("Today's Schedule")
        st.table(
            [
                {
                    "time": task.scheduled_for.strftime("%I:%M %p") if task.scheduled_for else "No time",
                    "pet": pet_names.get(task.pet_id, f"Pet #{task.pet_id}"),
                    "task": task.description,
                    "priority": task.priority,
                }
                for task in plan
            ]
        )
        conflict_warnings = scheduler.detect_schedule_conflicts(plan_date, include_completed=False)
        explanation_text, explanation_source = explain_plan_with_fallback(
            owner=owner,
            plan=plan,
            plan_reasons=scheduler.plan_reasons,
            target_date=plan_date,
            conflict_warnings=conflict_warnings,
            explainer=st.session_state.ai_explainer,
        )
        logger.info("Streamlit explanation mode selected: %s", explanation_source)

        st.markdown("### Why this plan")
        if explanation_source == "ai":
            st.caption("Explanation mode: AI (Gemini)")
        else:
            st.caption("Explanation mode: deterministic fallback")
            if st.session_state.ai_explainer_error:
                st.info(f"AI unavailable: {st.session_state.ai_explainer_error}")

        if conflict_warnings:
            st.markdown("### Conflict checks")
            for warning in conflict_warnings:
                st.warning(warning)

        st.markdown(explanation_text)
