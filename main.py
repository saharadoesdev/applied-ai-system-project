from datetime import date, datetime

from pawpal_system import Owner, Pet, Scheduler, Task


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

	print("Today's Schedule")
	print("-" * 16)

	if not plan:
		print("No tasks scheduled for today.")
		return

	for task in plan:
		time_text = task.scheduled_for.strftime("%I:%M %p") if task.scheduled_for else "No time"
		print(f"{time_text} | Pet #{task.pet_id} | {task.description} (Priority {task.priority})")


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


if __name__ == "__main__":
	scheduler = build_demo_data()
	print_todays_schedule(scheduler)
	print_filter_demo(scheduler)
	print_conflict_warnings(scheduler)
