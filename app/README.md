# Resume Parsing Engine App

## Scope of this README

This document describes only what currently exists in the app codebase and what has been implemented so far.

It does not describe planned features unless they are explicitly marked as not implemented.

## Current objective implemented

The app currently implements a deterministic resume parsing pipeline across two completed stages.

1. Phase 1

- Input validation
- Skill normalization
- Skill mapping from structured input

1. Phase 2

- Signal computation
- Proficiency scoring
- Confidence scoring
- Template reasoning generation
- Final response assembly

## App structure (current)

- Entry API: [app/main.py](main.py)
- Pipeline orchestration: [app/pipeline/resume_pipeline.py](pipeline/resume_pipeline.py)
- Request schema: [app/schemas/request.py](schemas/request.py)
- Internal schema: [app/schemas/internal.py](schemas/internal.py)
- Parse endpoint module: [app/api/endpoints/parse.py](api/endpoints/parse.py)
- Tests: [app/tests/test_phase2_engine.py](tests/test_phase2_engine.py)

### Implemented Phase 1 modules

- Validator: [app/modules/validation/input_validator.py](modules/validation/input_validator.py)
- Normalizer: [app/modules/normalization/skill_normalizer.py](modules/normalization/skill_normalizer.py)
- Mapper: [app/modules/extraction/skill_mapper.py](modules/extraction/skill_mapper.py)

### Implemented Phase 2 modules

- Signals: [app/modules/enrichment/signal_builder.py](modules/enrichment/signal_builder.py)
- Proficiency scoring: [app/modules/scoring/proficiency_engine.py](modules/scoring/proficiency_engine.py)
- Confidence scoring: [app/modules/scoring/confidence_engine.py](modules/scoring/confidence_engine.py)
- Reasoning: [app/modules/reasoning/reasoning_engine.py](modules/reasoning/reasoning_engine.py)
- Response assembly: [app/modules/assembly/response_builder.py](modules/assembly/response_builder.py)

## Data contract currently supported

Input expected by pipeline and endpoint:

- skills: list of strings
- projects: list of objects
- experience: list of objects

Request model is defined in [app/schemas/request.py](schemas/request.py).

## End-to-end pipeline (current implementation)

The function [app/pipeline/resume_pipeline.py](pipeline/resume_pipeline.py) executes this exact sequence.

1. validate_input
1. normalize_skills
1. map_skills
1. build_signals
1. compute_proficiency
1. compute_confidence
1. generate_reasoning
1. build_response

Returned value is the final assembled response object.

## Phase 1 details implemented

### Input validation

File: [app/modules/validation/input_validator.py](modules/validation/input_validator.py)

What it does now:

- Requires top-level keys: skills, projects, experience
- Validates top-level list types
- Validates skill item type is string
- Drops null and empty values for skills, projects, experience entries
- Raises ValueError for invalid shape and invalid types

### Skill normalization

File: [app/modules/normalization/skill_normalizer.py](modules/normalization/skill_normalizer.py)

What it does now:

- Lowercases and trims each skill
- Deduplicates while preserving first-seen normalized order
- Applies variant mapping:
  - nodejs -> node.js
  - node -> node.js
  - node js -> node.js
  - py -> python
- Raises ValueError for non-string or empty-string skills

### Skill mapping

File: [app/modules/extraction/skill_mapper.py](modules/extraction/skill_mapper.py)

What it does now:

- Builds internal skill records containing:
  - name
  - listed
  - projects
  - experience_months
  - evidence
- Scans project descriptions for non-overlapping alias mentions
- Scans experience descriptions for non-overlapping alias mentions
- Adds exact description strings as evidence
- Parses durations in month range format like Jan 2023 - Jun 2023
- Uses inclusive month calculation
- If duration parsing fails, contributes 0 months
- Keeps deterministic key order by sorting skills

## Phase 2 details implemented

### Signal builder

File: [app/modules/enrichment/signal_builder.py](modules/enrichment/signal_builder.py)

Signals added per skill:

- frequency = min(projects / 3, 1.0)
- duration = min(experience_months / 24, 1.0)
- complexity:
  - 0.7 if projects >= 2
  - 0.5 if projects == 1
  - 0.2 otherwise
- recency:
  - 0.9 if experience_months > 0
  - 0.7 else if projects > 0
  - 0.3 otherwise
- All values clamped to the range [0, 1]

### Proficiency engine

File: [app/modules/scoring/proficiency_engine.py](modules/scoring/proficiency_engine.py)

Score formula currently implemented:

- score = 0.2 x listed + 0.3 x frequency + 0.3 x duration + 0.2 x recency
- listed is 1.0 when listed is true, else 0.0
- score is clamped to [0, 1] and rounded to 4 decimals

Level mapping currently implemented:

- score < 0.4 -> beginner
- 0.4 <= score <= 0.7 -> intermediate
- score > 0.7 -> advanced

### Confidence engine

File: [app/modules/scoring/confidence_engine.py](modules/scoring/confidence_engine.py)

Confidence formula currently implemented:

- +0.4 if projects > 0
- +0.4 if experience_months > 0
- +0.2 if evidence list is non-empty
- Capped at 1.0
- Rounded to 4 decimals

### Reasoning engine

File: [app/modules/reasoning/reasoning_engine.py](modules/reasoning/reasoning_engine.py)

Reasoning generation currently implemented:

- Fully template based
- Uses listed, projects, and experience_months only
- Produces deterministic text variants such as:
  - used in X projects and Y months experience
  - listed skill used in X projects
  - listed skill with Y months experience
  - listed skill with no practical usage
  - detected skill with no practical usage

### Response builder

File: [app/modules/assembly/response_builder.py](modules/assembly/response_builder.py)

Final response format currently returned:

- version
- candidate_profile.skills list of objects with:
  - name
  - score
  - level
  - confidence
  - reasoning
  - evidence
- meta.total_skills

## API behavior currently implemented

### FastAPI app

File: [app/main.py](main.py)

Current behavior:

- Initializes FastAPI app
- Exposes POST /parse-resume
- Accepts request payload via ResumeRequest model
- Runs full pipeline and returns:
  - parsed: final response
- Converts ValueError into HTTP 400
- Includes a local sample execution block in the main guard

### Endpoint module

File: [app/api/endpoints/parse.py](api/endpoints/parse.py)

Current behavior:

- Declares APIRouter
- Exposes POST /parse-resume that returns parsed pipeline output

## Determinism and explainability status

Current implementation characteristics:

- Deterministic: yes
- Randomness used: no
- LLM calls in active pipeline: no
- Confidence and score formulas: explicit and fixed
- Reasoning generation: template based only
- Evidence source: input substrings only from project or experience descriptions

## Tests currently present

File: [app/tests/test_phase2_engine.py](tests/test_phase2_engine.py)

Current tests cover:

1. Signal formulas
1. Proficiency score and level
1. Confidence formula and cap
1. Reasoning template outputs
1. Response contract fields
1. End-to-end sample resume output checks
1. Determinism check by repeated pipeline execution

## Verified test status (latest run)

Command run:

- python -m pytest -q

Result:

- 7 passed
- 0 failed

## Dependencies currently tracked

File: [app/requirements.txt](requirements.txt)

Currently listed:

- fastapi==0.116.1
- pydantic==2.11.7
- uvicorn==0.35.0
- pytest==8.3.5

## How to run locally

From the app directory:

1. Create or activate virtual environment.
1. Install dependencies:
   - python -m pip install -r requirements.txt
1. Run tests:
   - python -m pytest -q
1. Run API:
   - python -m uvicorn main:app --reload

## Current sample output behavior

For the sample input used in tests and main:

- python is present in candidate_profile.skills
- python score is deterministic
- python level is intermediate
- confidence is greater than zero
- reasoning is non-empty
- evidence is non-empty
- total_skills equals 3 for that sample

## Known placeholders and non-implemented files in app

The following files exist but are currently empty placeholders in this repository state:

- [app/modules/services/external/git_hub.py](modules/services/external/git_hub.py)
- [app/modules/services/llm/clients.py](modules/services/llm/clients.py)
- [app/modules/services/llm/llm_services.py](modules/services/llm/llm_services.py)
- [app/modules/services/llm/prompts.py](modules/services/llm/prompts.py)
- [app/modules/normalization/date_parser.py](modules/normalization/date_parser.py)
- [app/modules/normalization/skill_normalization.py](modules/normalization/skill_normalization.py)
- [app/modules/enrichment/skill_aggregator.py](modules/enrichment/skill_aggregator.py)
- [app/modules/enrichment/skill_graph.py](modules/enrichment/skill_graph.py)
- [app/modules/reasoning/reasoning \_enginr.py](modules/reasoning/reasoning%20_enginr.py)

Also present are legacy typo-path folders not used by the active pipeline:

- [app/schemes](schemes)
- [app/modules/validaton](modules/validaton)

## What has not been implemented in the active pipeline

Based on current code, these are not part of active runtime flow:

- Any LLM integration
- External API integrations
- Gap endpoint logic in [app/api/endpoints/gap.py](api/endpoints/gap.py)
- Additional scoring or enrichment beyond the formulas documented above

## Source of truth files

If this README and code differ, code is authoritative in:

- [app/pipeline/resume_pipeline.py](pipeline/resume_pipeline.py)
- [app/modules](modules)
- [app/tests/test_phase2_engine.py](tests/test_phase2_engine.py)
