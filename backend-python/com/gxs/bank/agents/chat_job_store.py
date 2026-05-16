"""In-memory background job store for long-running chat requests.

This keeps the HTTP request responsive while the actual agent work runs in a
thread pool. Jobs are intentionally ephemeral and process-local; they are best
used for short-lived polling within a single backend process.
"""

from __future__ import annotations

import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable


_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="chat-job")
_LOCK = Lock()
_JOBS: dict[str, "JobRecord"] = {}


@dataclass
class JobRecord:
    job_id: str
    kind: str
    status: str
    created_at: float
    updated_at: float
    future: Future | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def _store(job: JobRecord) -> None:
    with _LOCK:
        _JOBS[job.job_id] = job


def _get(job_id: str) -> JobRecord | None:
    with _LOCK:
        return _JOBS.get(job_id)


def submit_job(kind: str, work_fn: Callable[[], dict[str, Any]], meta: dict[str, Any] | None = None) -> str:
    """Submit a job to the shared thread pool and return its job id."""
    job_id = uuid.uuid4().hex
    now = time.time()
    job = JobRecord(
        job_id=job_id,
        kind=kind,
        status="queued",
        created_at=now,
        updated_at=now,
        meta=meta or {},
    )
    _store(job)

    def _runner() -> dict[str, Any]:
        job.status = "running"
        job.updated_at = time.time()
        try:
            result = work_fn()
            job.result = result
            job.status = "completed"
            return result
        except Exception as exc:
            job.error = str(exc)
            job.status = "failed"
            raise
        finally:
            job.updated_at = time.time()

    future = _EXECUTOR.submit(_runner)
    job.future = future
    return job_id


def wait_for_job(job_id: str, timeout: float = 0.5) -> dict[str, Any] | None:
    """Return the result immediately if it completes before timeout."""
    job = _get(job_id)
    if not job or not job.future:
        return None
    try:
        result = job.future.result(timeout=timeout)
        if isinstance(result, dict):
            return result
        return {"result": result}
    except TimeoutError:
        return None


def job_status(job_id: str) -> dict[str, Any] | None:
    """Return the current status snapshot for a job."""
    job = _get(job_id)
    if not job:
        return None

    data: dict[str, Any] = {
        "job_id": job.job_id,
        "kind": job.kind,
        "status": job.status,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "meta": job.meta,
    }
    if job.result is not None:
        data["result"] = job.result
    if job.error:
        data["error"] = job.error
    if job.future and job.future.done() and job.status == "completed" and job.result is None:
        try:
            data["result"] = job.future.result()
        except Exception as exc:
            data["status"] = "failed"
            data["error"] = str(exc)
    return data
