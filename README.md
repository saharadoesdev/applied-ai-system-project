# PawPal+ (Module 2 Project)

## Original Project

The original project was **PawPal+**. Its goal was to help a pet owner manage care tasks by storing owner/pet/task data, generating a daily schedule, and surfacing scheduling conflicts. The core system focused on deterministic planning logic (time, priority, recurrence, completion status) and clear schedule output through both a CLI demo and a Streamlit interface.

## Updated Project Summary

**New Version:** PawPal+ with AI Plan Explanations and Reliability Guardrails

**Summary:** This updated version keeps deterministic pet-care scheduling as the source of truth and adds an AI explanation layer to make plan decisions easier to understand. When Gemini is available, the system generates concise natural-language schedule explanations; when it is unavailable or errors, it safely falls back to deterministic text. This matters because it improves usability while preserving reliability, reproducibility, and testable behavior.

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Configure Gemini key for AI mode.

```bash
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
```

Add your key to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

If the key is missing, the project still runs using deterministic fallback explanations.

### Run

Streamlit app:

```bash
streamlit run app.py
```

Terminal demo:

```bash
python main.py
```

Tests:

```bash
pytest -q
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
