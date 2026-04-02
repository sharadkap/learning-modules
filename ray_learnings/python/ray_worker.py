"""
ray_worker.py — RabbitMQ consumer that fans tasks out to Ray remote functions.

Architecture:
    RabbitMQ (AMQP) ──► pika consumer ──► dispatch() ──► Ray remote functions
                                                      ──► result → AMQP result queue

The pika consumer handles queue I/O on the main thread.
Ray remote functions execute in parallel across available CPU cores.
ray.get() collects results synchronously before acking the AMQP message.

Prerequisites:
    RabbitMQ running:  docker compose up -d rabbitmq  (in message_brokers/)
    pip install -r requirements.txt

Run (Terminal 1, from ray_learnings/python/):
    python ray_worker.py

Then (Terminal 2):
    python ray_producer.py
"""

import json
import time
import pika
import ray

BROKER_HOST = "localhost"
TASK_QUEUE = "ray_tasks"
RESULT_QUEUE = "ray_results"


# ── Ray Remote Functions ───────────────────────────────────────────────────────

@ray.remote
def compute_task(n: int) -> int:
    """CPU-bound computation: sum of squares up to n."""
    return sum(i * i for i in range(n))


@ray.remote
def slow_task(job_id: str, duration: float) -> dict:
    """Simulates a slow I/O-bound job."""
    time.sleep(duration)
    return {"job_id": job_id, "status": "done", "duration": duration}


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
    ch.basic_qos(prefetch_count=4)  # up to 4 unacknowledged messages at once
    return conn, ch


def publish_result(ch: pika.channel.Channel, task_id: str, payload: dict) -> None:
    ch.basic_publish(
        exchange="",
        routing_key=RESULT_QUEUE,
        body=json.dumps({"task_id": task_id, **payload}),
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent
            content_type="application/json",
        ),
    )


# ── Task Dispatch ──────────────────────────────────────────────────────────────

def dispatch(message: dict) -> ray.ObjectRef:
    """Route an AMQP message to the appropriate Ray remote function."""
    task_type = message.get("type")
    payload = message.get("payload", {})

    if task_type == "compute":
        return compute_task.remote(payload["n"])
    elif task_type == "slow":
        return slow_task.remote(payload["job_id"], payload["duration"])
    else:
        raise ValueError(f"Unknown task type: {task_type!r}")


# ── Message Handler ────────────────────────────────────────────────────────────

def on_message(
    ch: pika.channel.Channel,
    method: pika.spec.Basic.Deliver,
    _props,
    body: bytes,
) -> None:
    message = json.loads(body)
    task_id = message.get("id", "unknown")
    print(f"[worker] Received {task_id}: type={message.get('type')}")

    try:
        ref = dispatch(message)
        result = ray.get(ref, timeout=30)
        print(f"[worker] Completed {task_id}: {result}")
        publish_result(ch, task_id, {"result": result})
    except Exception as exc:
        print(f"[worker] Failed {task_id}: {exc}")
        publish_result(ch, task_id, {"error": str(exc)})

    ch.basic_ack(delivery_tag=method.delivery_tag)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Initialising Ray (local cluster, 4 CPUs)...")
    ray.init(num_cpus=4, ignore_reinit_error=True)

    print(f"Connecting to RabbitMQ at {BROKER_HOST}:5672...")
    conn, ch = connect()
    ch.basic_consume(queue=TASK_QUEUE, on_message_callback=on_message)

    print(f"[worker] Listening on '{TASK_QUEUE}'. Press Ctrl+C to stop.\n")
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        print("\n[worker] Shutting down...")
        ch.stop_consuming()
        conn.close()
        ray.shutdown()
