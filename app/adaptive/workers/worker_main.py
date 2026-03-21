"""
Unified in-process worker loop for adaptive queue tasks.

This is intentionally simple and suitable for local/dev and basic container runs.
"""

from __future__ import annotations

import os
import time

from app.adaptive.workers import expansion_worker, pathway_worker, trace_worker


POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "0.5"))


def run_forever() -> None:
    while True:
        did_work = False

        for worker in (pathway_worker, trace_worker, expansion_worker):
            result = worker.run_once()
            if result is not None:
                did_work = True

        if not did_work:
            time.sleep(max(0.1, POLL_SECONDS))


if __name__ == "__main__":
    run_forever()
