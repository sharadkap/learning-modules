"""
celery_worker.py — Starts the Celery worker process.

Prerequisites (from celery_learnings/ root):
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    Start RabbitMQ (from message_brokers/):
        docker compose up -d rabbitmq

Run (Terminal 1, from celery_learnings/python/):
    python celery_worker.py

Then (Terminal 2):
    python celery_producer.py
"""

import os
import sys

# Ensure the python/ directory is on sys.path so celery_tasks is importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_tasks import app  # noqa: E402

if __name__ == "__main__":
    print("Starting Celery worker — consuming from RabbitMQ amqp://localhost:5672")
    print("Workers: 2 concurrent processes")
    print("Press Ctrl+C to stop.\n")
    app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=2",
            "--hostname=worker@%h",
        ]
    )
