"""
celery_tasks.py — Celery application and all task definitions.

Requires RabbitMQ on localhost:5672 (guest/guest).
Start RabbitMQ from message_brokers/:
    docker compose up -d rabbitmq

This file is a shared module. Do not run directly.
Start worker:  python celery_worker.py
Send tasks:    python celery_producer.py
"""

import time
from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# ── Celery App ─────────────────────────────────────────────────────────────────
app = Celery(
    "celery_demo",
    broker="amqp://guest:guest@localhost:5672//",
    backend="rpc://",
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          # Ack only after the task completes
    worker_prefetch_multiplier=1, # One task per worker slot at a time
)


# ── Basic Tasks ────────────────────────────────────────────────────────────────

@app.task(bind=True, name="tasks.add")
def add(self, x: int, y: int) -> int:
    """Add two numbers."""
    logger.info("add(%s, %s)", x, y)
    return x + y


@app.task(bind=True, name="tasks.multiply")
def multiply(self, x: int, y: int) -> int:
    """Multiply two numbers."""
    logger.info("multiply(%s, %s)", x, y)
    return x * y


# ── Long-Running Task with Progress States ─────────────────────────────────────

@app.task(bind=True, name="tasks.slow_job", max_retries=3, default_retry_delay=5)
def slow_job(self, job_id: str, duration: float = 2.0) -> dict:
    """
    Simulates a slow external job.
    Tracks PENDING → STARTED → PROGRESS → SUCCESS lifecycle.
    Retries automatically on failure (up to max_retries).
    """
    logger.info("slow_job start: job_id=%s, duration=%ss", job_id, duration)
    try:
        self.update_state(state="PROGRESS", meta={"job_id": job_id, "progress": 0})
        time.sleep(duration * 0.5)
        self.update_state(state="PROGRESS", meta={"job_id": job_id, "progress": 50})
        time.sleep(duration * 0.5)
        result = {"job_id": job_id, "status": "done", "duration": duration}
        logger.info("slow_job done: %s", result)
        return result
    except Exception as exc:
        logger.warning("slow_job retrying: %s", exc)
        raise self.retry(exc=exc)


# ── Pipeline / Composition Tasks ───────────────────────────────────────────────

@app.task(bind=True, name="tasks.transform")
def transform(self, value: int, op: str = "square") -> int:
    """
    Transforms a value. Designed as a composable chain step.
    op: 'square' | 'double' | 'negate'
    """
    ops = {
        "square": lambda v: v * v,
        "double": lambda v: v * 2,
        "negate": lambda v: -v,
    }
    result = ops.get(op, lambda v: v)(value)
    logger.info("transform %s(%s) = %s", op, value, result)
    return result


@app.task(bind=True, name="tasks.summarise")
def summarise(self, results: list) -> dict:
    """
    Aggregates a list of results.
    Used as the chord callback after a parallel group completes.
    """
    total = sum(results)
    logger.info("summarise: results=%s total=%s", results, total)
    return {"results": results, "total": total, "count": len(results)}


if __name__ == "__main__":
    print("This module defines tasks. Start the worker with:")
    print("  python celery_worker.py")
    print("  or: celery -A celery_tasks worker --loglevel=info")
