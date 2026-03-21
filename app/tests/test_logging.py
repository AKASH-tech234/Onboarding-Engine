import io
import logging
from contextlib import contextmanager

import pipeline.resume_pipeline as resume_pipeline
from pipeline.resume_pipeline import run_pipeline


@contextmanager
def _capture_named_logs(names: list[str]):
    stream = io.StringIO()
    formatter = logging.Formatter("[%(levelname)s] %(name)s | %(message)s")
    attached: list[tuple[logging.Logger, logging.Handler]] = []

    try:
        for name in names:
            logger = logging.getLogger(name)
            handler = logging.StreamHandler(stream)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            attached.append((logger, handler))
        yield stream
    finally:
        for logger, handler in attached:
            logger.removeHandler(handler)


def test_pipeline_emits_stage_logs() -> None:
    sample = {
        "skills": ["Python", "Java"],
        "projects": [
            {
                "name": "Compiler",
                "description": "An improvement over Booth's algorithm in Python",
            }
        ],
        "experience": [],
        "debug": True,
    }

    with _capture_named_logs(["pipeline", "validation", "normalization", "mapper", "signals", "scoring", "confidence", "reasoning", "response"]):
        result = run_pipeline(sample)

    assert "candidate_profile" in result

    with _capture_named_logs(["pipeline", "validation", "normalization", "mapper", "signals", "scoring", "confidence", "reasoning", "response"]) as stream:
        run_pipeline(sample)
        logs = stream.getvalue()

    assert "Starting pipeline" in logs
    assert "After validation" in logs
    assert "After normalization" in logs
    assert "Mapped skills" in logs
    assert "Signals" in logs
    assert "Scores" in logs
    assert "Confidence" in logs
    assert "Final response" in logs


def test_pipeline_logs_llm_failure_path() -> None:
    sample = {
        "skills": ["Python"],
        "projects": [
            {
                "name": "Algo",
                "description": "An improvement over Booth's algorithm",
            }
        ],
        "experience": [],
    }

    with _capture_named_logs(["pipeline", "llm"]) as stream:
        run_pipeline(sample)
        logs = stream.getvalue()

    assert "LLM input" in logs
    assert (
        "Gemini API key not configured" in logs
        or "LLM raw output" in logs
        or "LLM call failed" in logs
        or "parse failed" in logs
        or "LLM output rejected" in logs
    )


def test_pipeline_logs_pathway_reason_code_on_failure(monkeypatch) -> None:
    sample = {
        "skills": ["python"],
        "projects": [],
        "experience": [],
    }
    jd = {
        "skills": ["machine learning"],
        "projects": [],
        "experience": [],
    }

    def _raise_pathway_failure(**_kwargs):
        raise ValueError("cycle_detected: synthetic")

    monkeypatch.setattr(resume_pipeline, "build_pathway", _raise_pathway_failure)

    with _capture_named_logs(["pipeline"]) as stream:
        result = run_pipeline(sample, jd_data=jd, include_pathway=True)
        logs = stream.getvalue()

    assert "pathway" in result
    assert result["pathway"]["meta"]["reason_code"] == "cycle_detected"
    assert "reason_code=cycle_detected" in logs
