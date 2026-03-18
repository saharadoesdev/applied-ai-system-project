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


def test_generate_daily_plan_returns_tasks_in_chronological_order() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	target_date = date(2026, 3, 18)

	later_task = Task(
		task_id=10,
		pet_id=101,
		description="Evening walk",
		scheduled_for=datetime(2026, 3, 18, 18, 0),
	)
	early_task = Task(
		task_id=11,
		pet_id=101,
		description="Morning feeding",
		scheduled_for=datetime(2026, 3, 18, 7, 0),
	)
	mid_task = Task(
		task_id=12,
		pet_id=101,
		description="Noon medicine",
		scheduled_for=datetime(2026, 3, 18, 12, 0),
	)

	pet.add_task(later_task)
	pet.add_task(early_task)
	pet.add_task(mid_task)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	plan = scheduler.generate_daily_plan(target_date)

	assert [task.task_id for task in plan] == [11, 12, 10]


def test_generate_daily_plan_sorts_by_priority_then_task_id_for_same_time() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	target_date = date(2026, 3, 18)

	high_priority = Task(
		task_id=21,
		pet_id=101,
		description="Urgent medication",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
		priority=5,
	)
	lower_priority = Task(
		task_id=20,
		pet_id=101,
		description="Regular walk",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
		priority=2,
	)
	same_priority_lower_id = Task(
		task_id=18,
		pet_id=101,
		description="Breakfast",
		scheduled_for=datetime(2026, 3, 18, 9, 0),
		priority=3,
	)
	same_priority_higher_id = Task(
		task_id=19,
		pet_id=101,
		description="Brush coat",
		scheduled_for=datetime(2026, 3, 18, 9, 0),
		priority=3,
	)

	pet.add_task(lower_priority)
	pet.add_task(high_priority)
	pet.add_task(same_priority_higher_id)
	pet.add_task(same_priority_lower_id)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	plan = scheduler.generate_daily_plan(target_date)

	assert [task.task_id for task in plan] == [21, 20, 18, 19]


def test_generate_daily_plan_returns_empty_for_pet_with_no_tasks() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	plan = scheduler.generate_daily_plan(date(2026, 3, 18))

	assert plan == []
	assert scheduler.explain_plan() == "No tasks scheduled for today."


def test_mark_task_complete_once_task_does_not_create_new_task() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	once_task = Task(
		task_id=1,
		pet_id=101,
		description="Vet check-in",
		scheduled_for=datetime(2026, 3, 18, 15, 0),
		frequency="once",
	)
	pet.add_task(once_task)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	result = scheduler.mark_task_complete(1)

	assert result is True
	assert once_task.is_completed is True
	assert len(pet.tasks) == 1


def test_daily_task_with_future_start_date_not_included_before_start() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	future_daily_task = Task(
		task_id=1,
		pet_id=101,
		description="Future recurring medicine",
		scheduled_for=datetime(2026, 3, 20, 8, 0),
		frequency="daily",
	)
	pet.add_task(future_daily_task)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	tasks_before_start = scheduler.get_tasks_for_date(date(2026, 3, 18))
	tasks_on_start = scheduler.get_tasks_for_date(date(2026, 3, 20))

	assert tasks_before_start == []
	assert tasks_on_start == [future_daily_task]


def test_detect_schedule_conflicts_ignores_completed_tasks_by_default() -> None:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=1)
	target_date = date(2026, 3, 18)

	completed_task = Task(
		task_id=1,
		pet_id=101,
		description="Completed walk",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
		is_completed=True,
	)
	pending_task = Task(
		task_id=2,
		pet_id=101,
		description="Pending breakfast",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
	)

	pet.add_task(completed_task)
	pet.add_task(pending_task)
	owner.add_pet(pet)
	scheduler = Scheduler(owner)

	default_warnings = scheduler.detect_schedule_conflicts(target_date)
	all_warnings = scheduler.detect_schedule_conflicts(target_date, include_completed=True)

	assert default_warnings == []
	assert len(all_warnings) == 1
	assert "08:00 AM conflict (same pet)" in all_warnings[0]
