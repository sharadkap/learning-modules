"""
celery_producer.py — Sends tasks to the Celery worker via RabbitMQ.

Demonstrates:
    1. Fire-and-forget (.delay)
    2. Synchronous result retrieval (.get)
    3. Task chaining  (add → square → double)
    4. Parallel groups  (N multiplications at once)
    5. Chords  (parallel group + summarise callback)
    6. Long-running task with progress polling
    7. Countdown (scheduled future execution)

Prerequisites:
    Worker must be running in Terminal 1: python celery_worker.py
    RabbitMQ must be running:            docker compose up -d rabbitmq

Run (Terminal 2, from celery_learnings/python/):
    python celery_producer.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import chain, chord, group  # noqa: E402
from celery_tasks import add, multiply, slow_job, summarise, transform  # noqa: E402

SEP = "─" * 60


def section(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


# ── 1. Fire-and-Forget ─────────────────────────────────────────────────────────

def demo_fire_and_forget() -> None:
    section("1. Fire-and-Forget  (.delay)")
    result = add.delay(10, 20)
    print(f"Task dispatched — ID: {result.id}")
    print(f"State before .get(): {result.state}")
    value = result.get(timeout=10)
    print(f"Result: 10 + 20 = {value}")


# ── 2. Synchronous Result ──────────────────────────────────────────────────────

def demo_sync_result() -> None:
    section("2. Synchronous Result  (.get)")
    result = multiply.delay(7, 6)
    value = result.get(timeout=10)
    print(f"7 × 6 = {value}")


# ── 3. Task Chain ──────────────────────────────────────────────────────────────

def demo_chain() -> None:
    section("3. Task Chain  add(3,4) → square → double")
    # add(3, 4) = 7 → square(7) = 49 → double(49) = 98
    pipeline = chain(
        add.s(3, 4),
        transform.s(op="square"),
        transform.s(op="double"),
    )
    result = pipeline.apply_async()
    value = result.get(timeout=15)
    print(f"Chain result: {value}  (expected 98)")


# ── 4. Parallel Group ──────────────────────────────────────────────────────────

def demo_group() -> None:
    section("4. Parallel Group  (4 multiplications in parallel)")
    tasks = group(multiply.s(i, i) for i in range(1, 5))
    results = tasks.apply_async().get(timeout=15)
    print(f"i×i for i in 1..4: {results}  (expected [1, 4, 9, 16])")


# ── 5. Chord ───────────────────────────────────────────────────────────────────

def demo_chord() -> None:
    section("5. Chord  (parallel group + summarise callback)")
    # Compute add(i, i*2) for i in 1..5, then aggregate
    header = group(add.s(i, i * 2) for i in range(1, 6))
    callback = summarise.s()
    result = chord(header)(callback)
    summary = result.get(timeout=20)
    print(f"Chord summary: {summary}")


# ── 6. Progress Tracking ───────────────────────────────────────────────────────

def demo_progress() -> None:
    section("6. Long-Running Task with Progress States")
    result = slow_job.delay("demo-job-001", duration=2.0)
    print(f"Task ID: {result.id}  — polling...")
    while not result.ready():
        state = result.state
        meta = result.info if isinstance(result.info, dict) else {}
        print(f"  State: {state:<12}  Meta: {meta}")
        time.sleep(0.4)
    print(f"Final result: {result.get(timeout=10)}")


# ── 7. Countdown ───────────────────────────────────────────────────────────────

def demo_countdown() -> None:
    section("7. Scheduled Execution  (countdown=3s)")
    result = add.apply_async((100, 200), countdown=3)
    print(f"Task scheduled 3s from now. ID: {result.id}")
    value = result.get(timeout=15)
    print(f"100 + 200 = {value}")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Celery Producer — dispatching tasks to RabbitMQ")
    print("Ensure the worker is running:  python celery_worker.py\n")

    demo_fire_and_forget()
    demo_sync_result()
    demo_chain()
    demo_group()
    demo_chord()
    demo_progress()
    demo_countdown()

    print(f"\n{SEP}\n  All demos complete.\n{SEP}")
