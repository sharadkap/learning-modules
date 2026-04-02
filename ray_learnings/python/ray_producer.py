"""
ray_producer.py — Publishes tasks to RabbitMQ for ray_worker.py to process.

Demonstrates the producer side of a Ray + RabbitMQ integration:
    - Publishes typed task messages (compute, slow) to RabbitMQ
    - Polls the result queue until all results are collected
    - Shows task IDs mapped to results

Prerequisites:
    RabbitMQ running:         docker compose up -d rabbitmq  (in message_brokers/)
    Ray worker listening:     python ray_worker.py  (Terminal 1)

Run (Terminal 2, from ray_learnings/python/):
    python ray_producer.py
"""

import json
import time
import uuid
import pika

BROKER_HOST = "localhost"
TASK_QUEUE = "ray_tasks"
RESULT_QUEUE = "ray_results"

SEP = "─" * 60


def section(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


# ── AMQP Helpers ───────────────────────────────────────────────────────────────

def connect() -> tuple[pika.BlockingConnection, pika.channel.Channel]:
    params = pika.ConnectionParameters(
        host=BROKER_HOST,
        credentials=pika.PlainCredentials("guest", "guest"),
        heartbeat=60,
    )
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=TASK_QUEUE, durable=True)
    ch.queue_declare(queue=RESULT_QUEUE, durable=True)
    return conn, ch


def publish_task(ch: pika.channel.Channel, task_type: str, payload: dict) -> str:
    task_id = str(uuid.uuid4())[:8]
    message = json.dumps({"id": task_id, "type": task_type, "payload": payload})
    ch.basic_publish(
        exchange="",
        routing_key=TASK_QUEUE,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent — survives broker restart
            content_type="application/json",
        ),
    )
    return task_id


def collect_results(
    ch: pika.channel.Channel, expected: int, timeout: float = 30.0
) -> list[dict]:
    results = []
    deadline = time.time() + timeout
    while len(results) < expected and time.time() < deadline:
        method, _, body = ch.basic_get(queue=RESULT_QUEUE, auto_ack=True)
        if method:
            results.append(json.loads(body))
        else:
            time.sleep(0.1)
    return results


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Ray Producer — publishing tasks to RabbitMQ")
    print("Ensure ray_worker.py is running in another terminal.\n")

    conn, ch = connect()
    all_task_ids: list[str] = []

    # 1. Publish compute tasks
    section("1. Publish 8 Compute Tasks")
    for i in range(1, 9):
        n = i * 200_000
        tid = publish_task(ch, "compute", {"n": n})
        all_task_ids.append(tid)
        print(f"  Published {tid}: compute(n={n:,})")

    # 2. Publish slow tasks
    section("2. Publish 4 Slow Tasks")
    for i in range(4):
        tid = publish_task(ch, "slow", {"job_id": f"job-{i}", "duration": 0.3})
        all_task_ids.append(tid)
        print(f"  Published {tid}: slow_task(job_id=job-{i}, duration=0.3s)")

    total = len(all_task_ids)
    print(f"\nPublished {total} tasks total. Waiting for results...")

    # 3. Collect results
    section(f"3. Collecting {total} Results (timeout=30s)")
    time.sleep(0.5)  # brief pause to let worker start consuming
    results = collect_results(ch, expected=total, timeout=30.0)

    print(f"Received {len(results)}/{total} results:")
    for r in sorted(results, key=lambda x: x.get("task_id", "")):
        print(f"  {r}")

    conn.close()
    print(f"\n{SEP}\n  Producer done.\n{SEP}")
