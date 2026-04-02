# Celery Learnings

Production-ready Celery task queue implementations covering worker lifecycle, task chaining, parallel groups, chords, beat scheduling, and RabbitMQ integration with Python.

## What You Will Learn

- How Celery decouples producers from workers via a broker (RabbitMQ)
- Task lifecycle: PENDING → STARTED → PROGRESS → SUCCESS / FAILURE
- Composing complex workflows with chains, groups, and chords
- Recurring tasks with Celery Beat
- Tuning workers for throughput and reliability

## Prerequisites

- Python 3.13+
- RabbitMQ running via the shared `message_brokers/` Docker Compose stack

## Setup

```bash
cd celery_learnings
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Start RabbitMQ

```bash
# From the message_brokers/ directory
docker compose up -d rabbitmq
```

RabbitMQ management UI: http://localhost:15672 (guest / guest)

## Running the Labs

All scripts live in `python/`. Run them from the `python/` directory:

```bash
cd celery_learnings/python
```

### Terminal 1 — Start the worker

```bash
python celery_worker.py
# or equivalently:
# celery -A celery_tasks worker --loglevel=info --concurrency=2
```

### Terminal 2 — Send tasks

```bash
python celery_producer.py
```

### Terminal 3 (optional) — Start Beat scheduler

```bash
python celery_beat.py
```

## Lab Implementation & Engineering Deep Dives

### 1. Task Definitions ([python/celery_tasks.py](./python/celery_tasks.py))

- **Why**: Central module defining the Celery app, broker/backend config, and all tasks.
- **What**: `add`, `multiply`, `slow_job` (with progress states), `transform` (chain step), `summarise` (chord callback).
- **How**: Uses `bind=True` for self-reference, `rpc://` backend for results over RabbitMQ, `acks_late=True` for at-least-once delivery.

### 2. Worker Process ([python/celery_worker.py](./python/celery_worker.py))

- **Why**: Demonstrates starting a worker programmatically.
- **What**: Calls `app.worker_main()` with concurrency=2, showing how worker lifecycle is managed.
- **How**: `app.worker_main(argv=[...])` mirrors the `celery worker` CLI.

### 3. Task Producer ([python/celery_producer.py](./python/celery_producer.py))

- **Why**: Shows every major task dispatch pattern in one runnable script.
- **What**: Fire-and-forget, result retrieval, chains, groups, chords, countdown scheduling.
- **How**: Uses `.delay()`, `.apply_async()`, `chain()`, `group()`, `chord()` from Celery.

### 4. Beat Scheduler ([python/celery_beat.py](./python/celery_beat.py))

- **Why**: Shows periodic task execution without external cron.
- **What**: Schedules `add` every 5s, `slow_job` every 15s, `multiply` every 60s.
- **How**: `app.conf.beat_schedule` dict + `app.start(["beat", "--loglevel=info"])`.
