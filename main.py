import logging
from datetime import date, datetime

from dotenv import load_dotenv

from ai_explainer import GeminiPlanExplainer, explain_plan_with_fallback
from pawpal_system import Owner, Pet, Scheduler, Task

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()


def build_demo_data() -> Scheduler:
	"""Create a demo owner, pets, and tasks for terminal-based scheduler checks."""
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)

	pet_one = Pet(pet_id=101, name="Milo", species="Dog", owner_id=owner.owner_id)
	pet_two = Pet(pet_id=102, name="Luna", species="Cat", owner_id=owner.owner_id)

	today = date.today()

	task_walk = Task(
		task_id=1,
		pet_id=pet_one.pet_id,
		description="Morning walk",
		scheduled_for=datetime(today.year, today.month, today.day, 8, 0),
		frequency="once",
		duration_minutes=30,
		priority=3,
	)
	task_brush = Task(
		task_id=4,
		pet_id=pet_one.pet_id,
		description="Brush coat",
		scheduled_for=datetime(today.year, today.month, today.day, 12, 0),
		frequency="once",
		duration_minutes=10,
		priority=1,
	)
	task_feed = Task(
		task_id=2,
		pet_id=pet_two.pet_id,
		description="Feed dinner",
		scheduled_for=datetime(today.year, today.month, today.day, 18, 0),
		frequency="once",
		duration_minutes=15,
		priority=2,
	)
	task_meds = Task(
		task_id=3,
		pet_id=pet_one.pet_id,
		description="Give medication",
		scheduled_for=datetime(today.year, today.month, today.day, 21, 0),
		frequency="once",
		duration_minutes=10,
		priority=5,
	)
	task_training = Task(
		task_id=5,
		pet_id=pet_one.pet_id,
		description="Training session",
		scheduled_for=datetime(today.year, today.month, today.day, 8, 0),
		frequency="once",
		duration_minutes=20,
		priority=4,
	)
	task_litter = Task(
		task_id=6,
		pet_id=pet_two.pet_id,
		description="Clean litter box",
		scheduled_for=datetime(today.year, today.month, today.day, 8, 0),
		frequency="once",
		duration_minutes=10,
		priority=3,
	)

	# Intentionally add tasks out of chronological order to demonstrate sorting.
	pet_one.add_task(task_meds)
	pet_one.add_task(task_walk)
	pet_one.add_task(task_brush)
	pet_one.add_task(task_training)
	pet_two.add_task(task_feed)
	pet_two.add_task(task_litter)
	task_feed.mark_done()

	owner.add_pet(pet_one)
	owner.add_pet(pet_two)

	return Scheduler(owner)


def print_todays_schedule(scheduler: Scheduler) -> None:
	"""Generate and print today's ordered schedule from the scheduler."""
	today = date.today()
	plan = scheduler.generate_daily_plan(today)
	pet_names_by_id = {pet.pet_id: pet.name for pet in scheduler.owner.pets}

	print("Today's Schedule")
	print("-" * 16)

	if not plan:
		print("No tasks scheduled for today.")
		return

	for task in plan:
		time_text = task.scheduled_for.strftime("%I:%M %p") if task.scheduled_for else "No time"
		pet_name = pet_names_by_id.get(task.pet_id, f"Pet #{task.pet_id}")
		print(f"{time_text} | {pet_name} | {task.description} (Priority {task.priority})")


def print_filter_demo(scheduler: Scheduler) -> None:
	"""Print examples of completion- and pet-based task filtering."""
	print("\nFilter Demo")
	print("-" * 11)

	pending_tasks = scheduler.filter_tasks(is_completed=False)
	completed_tasks = scheduler.filter_tasks(is_completed=True)
	milo_tasks = scheduler.filter_tasks(pet_name="Milo")

	print("Pending tasks:")
	for task in pending_tasks:
		print(f"- {task.description}")

	print("Completed tasks:")
	for task in completed_tasks:
		print(f"- {task.description}")

	print("Tasks for Milo:")
	for task in milo_tasks:
		print(f"- {task.description}")


def print_conflict_warnings(scheduler: Scheduler) -> None:
	"""Print non-blocking warning messages for same-time scheduling conflicts."""
	print("\nConflict Warnings")
	print("-" * 17)

	warnings = scheduler.detect_schedule_conflicts(date.today(), include_completed=False)
	if not warnings:
		print("No schedule conflicts detected.")
		return

	for warning in warnings:
		print(warning)


def print_ai_summary(scheduler: Scheduler) -> None:
	"""Print the AI explanation for today's generated plan, with a deterministic fallback."""
	today = date.today()
	plan = scheduler.generate_daily_plan(today)

	print("\nAI Summary")
	print("-" * 10)

	if not plan:
		print("No tasks scheduled for today.")
		return

	conflict_warnings = scheduler.detect_schedule_conflicts(today, include_completed=False)

	try:
		explainer = GeminiPlanExplainer()
		ai_error = ""
		logger.info("CLI AI explainer initialized")
	except RuntimeError as error:
		explainer = None
		ai_error = str(error)
		logger.warning("CLI running without AI explainer: %s", error)

	text, source = explain_plan_with_fallback(
		owner=scheduler.owner,
		plan=plan,
		plan_reasons=scheduler.plan_reasons,
		target_date=today,
		conflict_warnings=conflict_warnings,
		explainer=explainer,
	)

	print(f"Mode: {'AI (Gemini)' if source == 'ai' else 'deterministic fallback'}")
	logger.info("CLI explanation mode selected: %s", source)
	if source != "ai" and ai_error:
		print(f"AI unavailable: {ai_error}")
	print(text)


if __name__ == "__main__":
	scheduler = build_demo_data()
	print_todays_schedule(scheduler)
	print_filter_demo(scheduler)
	print_conflict_warnings(scheduler)
	print_ai_summary(scheduler)
