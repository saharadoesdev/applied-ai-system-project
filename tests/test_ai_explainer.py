from datetime import date, datetime

from ai_explainer import build_fallback_explanation, explain_plan_with_fallback
from pawpal_system import Owner, Pet, Task


class WorkingExplainer:
	def explain_plan(self, **_: object) -> str:
		return "AI explanation text"


class FailingExplainer:
	def explain_plan(self, **_: object) -> str:
		raise RuntimeError("Simulated API failure")


def _build_owner_and_plan() -> tuple[Owner, list[Task], dict[int, str]]:
	owner = Owner(owner_id=1, name="Sahara", available_minutes_per_day=180)
	pet = Pet(pet_id=101, name="Milo", species="Dog", owner_id=owner.owner_id)
	owner.add_pet(pet)

	task = Task(
		task_id=1,
		pet_id=pet.pet_id,
		description="Morning walk",
		scheduled_for=datetime(2026, 3, 18, 8, 0),
		priority=3,
	)
	pet.add_task(task)
	plan = [task]
	plan_reasons = {1: "Included because it is due today"}
	return owner, plan, plan_reasons


def test_build_fallback_explanation_includes_reason_text() -> None:
	_, plan, plan_reasons = _build_owner_and_plan()

	text = build_fallback_explanation(plan, plan_reasons)

	assert "fallback mode" in text.lower()
	assert "Morning walk" in text
	assert "Included because it is due today" in text


def test_explain_plan_with_fallback_uses_fallback_when_no_explainer() -> None:
	owner, plan, plan_reasons = _build_owner_and_plan()

	text, source = explain_plan_with_fallback(
		owner=owner,
		plan=plan,
		plan_reasons=plan_reasons,
		target_date=date(2026, 3, 18),
		conflict_warnings=[],
		explainer=None,
	)

	assert source == "fallback"
	assert "Plan rationale" in text


def test_explain_plan_with_fallback_uses_fallback_when_ai_errors() -> None:
	owner, plan, plan_reasons = _build_owner_and_plan()

	text, source = explain_plan_with_fallback(
		owner=owner,
		plan=plan,
		plan_reasons=plan_reasons,
		target_date=date(2026, 3, 18),
		conflict_warnings=[],
		explainer=FailingExplainer(),
	)

	assert source == "fallback"
	assert "Plan rationale" in text


def test_explain_plan_with_fallback_uses_ai_when_available() -> None:
	owner, plan, plan_reasons = _build_owner_and_plan()

	text, source = explain_plan_with_fallback(
		owner=owner,
		plan=plan,
		plan_reasons=plan_reasons,
		target_date=date(2026, 3, 18),
		conflict_warnings=[],
		explainer=WorkingExplainer(),
	)

	assert source == "ai"
	assert text == "AI explanation text"
