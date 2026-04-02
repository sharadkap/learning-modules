"""
celery_beat.py — Celery Beat periodic task scheduler.

Beat reads a schedule and publishes tasks to RabbitMQ automatically.
The worker (celery_worker.py) must be running to execute those tasks.

Prerequisites:
    Worker running in Terminal 1: python celery_worker.py
    RabbitMQ running:             docker compose up -d rabbitmq

Run (Terminal 3, from celery_learnings/python/):
    python celery_beat.py

You can also run worker + beat together in one process:
    celery -A celery_tasks worker --beat --loglevel=info
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_tasks import app  # noqa: E402

# ── Beat Schedule ──────────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Simple arithmetic — fires every 5 seconds
    "add-every-5s": {
        "task": "tasks.add",
        "schedule": 5.0,
        "args": (1, 1),
    },
    # Slow job — fires every 15 seconds
    "slow-job-every-15s": {
        "task": "tasks.slow_job",
        "schedule": 15.0,
        "kwargs": {"job_id": "beat-job", "duration": 1.0},
    },
    # Multiply — fires every 60 seconds
    "multiply-every-60s": {
        "task": "tasks.multiply",
        "schedule": 60.0,
        "args": (3, 7),
    },
}

app.conf.timezone = "UTC"

if __name__ == "__main__":
    print("Starting Celery Beat scheduler...")
    print("Active schedule:")
    for name, entry in app.conf.beat_schedule.items():
        print(f"  {name:<25} task={entry['task']}, every={entry['schedule']}s")
    print("\nPress Ctrl+C to stop.\n")
    app.start(argv=["beat", "--loglevel=info"])
