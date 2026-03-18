from datetime import date, datetime, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_task_completion_marks_task_done() -> None:
	task = Task(task_id=1, pet_id=101, description="Morning walk")

	task.mark_done()

	assert task.is_completed is True


def test_add_task_increases_pet_task_count() -> None:
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	initial_count = len(pet.tasks)
	task = Task(task_id=2, pet_id=101, description="Feed breakfast")

	pet.add_task(task)

	assert len(pet.tasks) == initial_count + 1


def test_scheduler_filter_tasks_by_completion_status() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	completed_task = Task(task_id=1, pet_id=101, description="Morning walk", is_completed=True)
	pending_task = Task(task_id=2, pet_id=101, description="Feed breakfast")

	pet.add_task(completed_task)
	pet.add_task(pending_task)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	completed = scheduler.filter_tasks(is_completed=True)
	pending = scheduler.filter_tasks(is_completed=False)

	assert completed == [completed_task]
	assert pending == [pending_task]


def test_scheduler_filter_tasks_by_pet_name() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	dog = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	cat = Pet(pet_id=102, name="Luna", species="Cat", owner_id=1)
	dog_task = Task(task_id=1, pet_id=101, description="Morning walk")
	cat_task = Task(task_id=2, pet_id=102, description="Feed dinner")

	dog.add_task(dog_task)
	cat.add_task(cat_task)
	owner.add_pet(dog)
	owner.add_pet(cat)
	scheduler = Scheduler(owner)

	assert scheduler.filter_tasks(pet_name="milo") == [dog_task]
	assert scheduler.filter_tasks(pet_name="LUNA") == [cat_task]


def test_mark_task_complete_creates_next_daily_task_instance() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	daily_task = Task(
		task_id=1,
		pet_id=101,
		description="Morning walk",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
		frequency="daily",
	)
	pet.add_task(daily_task)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	result = scheduler.mark_task_complete(1)
	expected_date = date.today() + timedelta(days=1)

	assert result is True
	assert daily_task.is_completed is True
	assert len(pet.tasks) == 2
	next_task = next(task for task in pet.tasks if task.task_id != 1)
	assert next_task.frequency == "daily"
	assert next_task.is_completed is False
	assert next_task.scheduled_for == datetime.combine(expected_date, datetime(2026, 3, 18, 8, 0).time())


def test_mark_task_complete_creates_next_weekly_task_instance() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	weekly_task = Task(
		task_id=1,
		pet_id=101,
		description="Sunday grooming",
		scheduled_for=datetime(2026, 3, 15, 10, 0),
		frequency="weekly",
	)
	pet.add_task(weekly_task)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	result = scheduler.mark_task_complete(1)
	expected_date = date.today() + timedelta(days=7)

	assert result is True
	assert weekly_task.is_completed is True
	assert len(pet.tasks) == 2
	next_task = next(task for task in pet.tasks if task.task_id != 1)
	assert next_task.frequency == "weekly"
	assert next_task.is_completed is False
	assert next_task.scheduled_for == datetime.combine(expected_date, datetime(2026, 3, 15, 10, 0).time())


def test_detect_schedule_conflicts_returns_warning_messages() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	dog = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	cat = Pet(pet_id=102, name="Luna", species="Cat", owner_id=1)

	target_date = date(2026, 3, 18)
	dog_walk = Task(
		task_id=1,
		pet_id=101,
		description="Morning walk",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
	)
	dog_training = Task(
		task_id=2,
		pet_id=101,
		description="Training session",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
	)
	dog_grooming = Task(
		task_id=3,
		pet_id=101,
		description="Grooming",
		scheduled_for=datetime(2026, 3, 18, 9, 0),
	)
	cat_feed = Task(
		task_id=4,
		pet_id=102,
		description="Feed breakfast",
		scheduled_for=datetime(2026, 3, 18, 9, 0),
	)

	dog.add_task(dog_walk)
	dog.add_task(dog_training)
	dog.add_task(dog_grooming)
	cat.add_task(cat_feed)

	owner.add_pet(dog)
	owner.add_pet(cat)
	scheduler = Scheduler(owner)

	warnings = scheduler.detect_schedule_conflicts(target_date)

	assert len(warnings) == 2
	assert any("08:00 AM conflict (same pet)" in warning for warning in warnings)
	assert any("09:00 AM conflict (different pets)" in warning for warning in warnings)
	assert any("Milo(Morning walk, Training session)" in warning for warning in warnings)
	assert any("Luna(Feed breakfast)" in warning for warning in warnings)
