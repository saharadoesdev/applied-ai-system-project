from __future__ import annotations

import logging
import os
import re
from datetime import date

from pawpal_system import Owner, Task

MODEL_NAME = "gemini-2.5-flash"
logger = logging.getLogger(__name__)


class GeminiPlanExplainer:
	"""Thin wrapper around Gemini for schedule explanation generation."""

	def __init__(self, model_name: str = MODEL_NAME) -> None:
		api_key = os.getenv("GEMINI_API_KEY")
		if not api_key:
			logger.warning("GeminiPlanExplainer initialization skipped: GEMINI_API_KEY not set")
			raise RuntimeError("Missing GEMINI_API_KEY")

		try:
			from google import genai
		except ImportError as exc:
			logger.exception("GeminiPlanExplainer initialization failed: google-genai package missing")
			raise RuntimeError(
				"google-genai is not installed. Add it to requirements and install dependencies."
			) from exc

		self._client = genai.Client(api_key=api_key)
		self._model_name = model_name
		logger.info("GeminiPlanExplainer initialized with model '%s'", model_name)

	def explain_plan(
		self,
		owner: Owner,
		plan: list[Task],
		pet_names_by_id: dict[int, str],
		plan_reasons: dict[int, str],
		target_date: date,
		conflict_warnings: list[str],
	) -> str:
		"""Return a plain-language explanation grounded in scheduler output."""
		logger.info(
			"Generating AI explanation for owner='%s' date='%s' tasks=%d conflicts=%d",
			owner.name,
			target_date.isoformat(),
			len(plan),
			len(conflict_warnings),
		)
		prompt = _build_prompt(owner, plan, pet_names_by_id, plan_reasons, target_date, conflict_warnings)
		response = self._client.models.generate_content(model=self._model_name, contents=prompt)
		response_text = (getattr(response, "text", "") or "").strip()
		if not response_text:
			logger.error("Gemini returned empty explanation text")
			raise RuntimeError("Gemini returned an empty explanation")
		logger.info("AI explanation generated successfully")
		return response_text


def _build_prompt(
	owner: Owner,
	plan: list[Task],
	pet_names_by_id: dict[int, str],
	plan_reasons: dict[int, str],
	target_date: date,
	conflict_warnings: list[str],
) -> str:
	lines: list[str] = []
	for task in plan:
		time_text = task.scheduled_for.strftime("%I:%M %p") if task.scheduled_for else "No time"
		pet_name = pet_names_by_id.get(task.pet_id, f"Pet #{task.pet_id}")
		reason = plan_reasons.get(task.task_id, "Included in today's plan")
		lines.append(
			f"- {time_text} | {pet_name} | {task.description} | "
			f"Priority {task.priority} | Frequency {task.frequency} | Reason: {reason}"
		)

	conflict_text = "\n".join(f"- {warning}" for warning in conflict_warnings) if conflict_warnings else "- None"

	plan_text = "\n".join(lines) if lines else "- None"

	return (
		"You are an assistant for a pet care scheduling app.\n"
		"Write a concise, friendly explanation of the schedule.\n"
		"Do not mention model rules or your own uncertainty unless there is a conflict.\n"
		"Use only the schedule details provided below.\n"
		"Prefer the pet's name over pet ids.\n"
		"Avoid repeating the same reason in multiple ways.\n\n"
		f"Owner: {owner.name}\n"
		f"Date: {target_date.isoformat()}\n"
		f"Available minutes per day: {owner.available_minutes_per_day}\n\n"
		"Plan items:\n"
		f"{plan_text}\n\n"
		"Conflict warnings:\n"
		f"{conflict_text}\n\n"
		"Output format:\n"
		"1) 1 short paragraph summary.\n"
		"2) 1 bullet per task.\n"
		"3) 1 final line that recommends exactly one first task to do right now.\n"
		"If multiple tasks share the earliest time, choose only one from the first listed task in Plan items.\n"
		"Keep it to 3 to 5 short sentences total if possible."
	)


def _first_step_line(plan: list[Task], pet_names_by_id: dict[int, str]) -> str:
	"""Return a deterministic single-task first-step recommendation."""
	if not plan:
		return "First step: No tasks scheduled for today."

	first_task = plan[0]
	time_text = first_task.scheduled_for.strftime("%I:%M %p") if first_task.scheduled_for else "No time"
	pet_name = pet_names_by_id.get(first_task.pet_id, f"Pet #{first_task.pet_id}")
	return f"First step: {first_task.description} for {pet_name} at {time_text}."


def _normalize_first_step_text(text: str, deterministic_first_step: str) -> str:
	"""Keep one clear first-action line by removing common duplicate phrasing."""
	if not text.strip():
		return deterministic_first_step

	duplicate_patterns = (
		r"^to begin.*",
		r"^start your day.*",
		r"^your first task(?:s)? .*",
		r"^the first task to do right now.*",
	)

	kept_lines: list[str] = []
	for raw_line in text.splitlines():
		line = raw_line.strip()
		if not line:
			kept_lines.append(raw_line)
			continue

		if line.lower().startswith("first step:"):
			continue

		if any(re.match(pattern, line.lower()) for pattern in duplicate_patterns):
			continue

		kept_lines.append(raw_line)

	cleaned = "\n".join(kept_lines).strip()
	if cleaned:
		return f"{cleaned}\n\n{deterministic_first_step}"
	return deterministic_first_step


def build_fallback_explanation(
	plan: list[Task],
	plan_reasons: dict[int, str],
	pet_names_by_id: dict[int, str],
) -> str:
	"""Build a deterministic explanation used when AI is unavailable."""
	if not plan:
		return "No tasks scheduled for today."

	lines = ["Plan rationale (fallback mode):"]
	for task in plan:
		time_text = task.scheduled_for.strftime("%I:%M %p") if task.scheduled_for else "No time"
		pet_name = pet_names_by_id.get(task.pet_id, f"Pet #{task.pet_id}")
		reason = plan_reasons.get(task.task_id, "Included in today's plan")
		lines.append(
			f"- {time_text} | {pet_name} | {task.description} (Priority {task.priority}): {reason}"
		)
	lines.append("")
	lines.append(_first_step_line(plan, pet_names_by_id))
	return "\n".join(lines)


def explain_plan_with_fallback(
	owner: Owner,
	plan: list[Task],
	plan_reasons: dict[int, str],
	target_date: date,
	conflict_warnings: list[str],
	explainer: GeminiPlanExplainer | None,
) -> tuple[str, str]:
	"""Return explanation text and source label: 'ai' or 'fallback'."""
	pet_names_by_id = {pet.pet_id: pet.name for pet in owner.pets}
	fallback = build_fallback_explanation(plan, plan_reasons, pet_names_by_id)

	if explainer is None:
		logger.info("Using fallback explanation because AI explainer is unavailable")
		return fallback, "fallback"

	try:
		text = explainer.explain_plan(
			owner=owner,
			plan=plan,
			pet_names_by_id=pet_names_by_id,
			plan_reasons=plan_reasons,
			target_date=target_date,
			conflict_warnings=conflict_warnings,
		)
		first_step = _first_step_line(plan, pet_names_by_id)
		logger.info("Using AI explanation mode")
		return _normalize_first_step_text(text, first_step), "ai"
	except Exception:
		logger.exception("AI explanation failed; falling back to deterministic explanation")
		return fallback, "fallback"
