from __future__ import annotations

import os
from datetime import date

from pawpal_system import Owner, Task

MODEL_NAME = "gemini-2.5-flash"


class GeminiPlanExplainer:
	"""Thin wrapper around Gemini for schedule explanation generation."""

	def __init__(self, model_name: str = MODEL_NAME) -> None:
		api_key = os.getenv("GEMINI_API_KEY")
		if not api_key:
			raise RuntimeError("Missing GEMINI_API_KEY")

		try:
			import google.generativeai as genai
		except ImportError as exc:
			raise RuntimeError(
				"google-generativeai is not installed. Add it to requirements and install dependencies."
			) from exc

		genai.configure(api_key=api_key)
		self._model = genai.GenerativeModel(model_name)

	def explain_plan(
		self,
		owner: Owner,
		plan: list[Task],
		plan_reasons: dict[int, str],
		target_date: date,
		conflict_warnings: list[str],
	) -> str:
		"""Return a plain-language explanation grounded in scheduler output."""
		prompt = _build_prompt(owner, plan, plan_reasons, target_date, conflict_warnings)
		response = self._model.generate_content(prompt)
		response_text = (getattr(response, "text", "") or "").strip()
		if not response_text:
			raise RuntimeError("Gemini returned an empty explanation")
		return response_text


def _build_prompt(
	owner: Owner,
	plan: list[Task],
	plan_reasons: dict[int, str],
	target_date: date,
	conflict_warnings: list[str],
) -> str:
	lines: list[str] = []
	for task in plan:
		time_text = task.scheduled_for.strftime("%I:%M %p") if task.scheduled_for else "No time"
		reason = plan_reasons.get(task.task_id, "Included in today's plan")
		lines.append(
			f"- {time_text} | Pet #{task.pet_id} | {task.description} | "
			f"Priority {task.priority} | Frequency {task.frequency} | Reason: {reason}"
		)

	conflict_text = "\n".join(f"- {warning}" for warning in conflict_warnings) if conflict_warnings else "- None"

	plan_text = "\n".join(lines) if lines else "- None"

	return (
		"You are an assistant for a pet care scheduling app.\n"
		"Explain the schedule clearly and avoid medical claims.\n"
		"Use only the schedule details provided below.\n\n"
		f"Owner: {owner.name}\n"
		f"Date: {target_date.isoformat()}\n"
		f"Available minutes per day: {owner.available_minutes_per_day}\n\n"
		"Plan items:\n"
		f"{plan_text}\n\n"
		"Conflict warnings:\n"
		f"{conflict_text}\n\n"
		"Output format:\n"
		"1) A short paragraph summarizing why this order makes sense.\n"
		"2) A bullet for each task explaining why it appears where it does.\n"
		"3) A final one-line recommendation for what to do first right now."
	)


def build_fallback_explanation(plan: list[Task], plan_reasons: dict[int, str]) -> str:
	"""Build a deterministic explanation used when AI is unavailable."""
	if not plan:
		return "No tasks scheduled for today."

	lines = ["Plan rationale (fallback mode):"]
	for task in plan:
		time_text = task.scheduled_for.strftime("%I:%M %p") if task.scheduled_for else "No time"
		reason = plan_reasons.get(task.task_id, "Included in today's plan")
		lines.append(
			f"- {time_text} | {task.description} (Priority {task.priority}): {reason}"
		)
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
	fallback = build_fallback_explanation(plan, plan_reasons)

	if explainer is None:
		return fallback, "fallback"

	try:
		text = explainer.explain_plan(
			owner=owner,
			plan=plan,
			plan_reasons=plan_reasons,
			target_date=target_date,
			conflict_warnings=conflict_warnings,
		)
		return text, "ai"
	except Exception:
		return fallback, "fallback"
