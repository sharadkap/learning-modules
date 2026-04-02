# Ray Learnings

Production-ready Ray distributed computing implementations covering remote functions, stateful actors, parallel execution patterns, and RabbitMQ-driven task ingestion with Python.

## What You Will Learn

- How Ray distributes work across local CPU cores (and remote nodes)
- Remote functions and object references — Ray's core abstraction
- Stateful actors: long-lived worker objects that serialise concurrent access
- Parallel execution: ray.get(), ray.wait(), and non-blocking patterns
- Integrating RabbitMQ as a task source: fan-out to Ray remote workers

## Prerequisites

- Python 3.13+
- RabbitMQ running via the shared `message_brokers/` Docker Compose stack (for ray_worker.py and ray_producer.py)

## Setup

```bash
cd ray_learnings
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Start RabbitMQ (for RabbitMQ integration labs)

```bash
# From the message_brokers/ directory
docker compose up -d rabbitmq
```

## Running the Labs

All scripts live in `python/`. Run from the `python/` directory:

```bash
cd ray_learnings/python
```

### Standalone Ray demo (no RabbitMQ needed)

```bash
python ray_basics.py
```

### RabbitMQ + Ray integration

```bash
# Terminal 1 — start the Ray worker (consumes RabbitMQ, fans out to Ray)
python ray_worker.py

# Terminal 2 — publish tasks to RabbitMQ
python ray_producer.py
```

## Lab Implementation & Engineering Deep Dives

### 1. Core Ray Concepts ([python/ray_basics.py](./python/ray_basics.py))

- **Why**: Demonstrates all core Ray abstractions in a single standalone script.
- **What**: Remote functions, parallel fan-out, stateful actors, ray.wait() for non-blocking progress, and dependent pipelines.
- **How**: `ray.init(num_cpus=4)` spins up a local cluster. `@ray.remote` converts functions and classes. `ray.get()` collects futures.

### 2. RabbitMQ Consumer + Ray Worker ([python/ray_worker.py](./python/ray_worker.py))

- **Why**: Shows the pattern of using a message broker as a task source for Ray.
- **What**: Connects to RabbitMQ, consumes tasks from `ray_tasks` queue, dispatches each to a Ray remote function, publishes results to `ray_results` queue.
- **How**: pika blocking consumer + `ray.get()` per message. `basic_qos(prefetch_count=4)` limits in-flight messages.

### 3. Task Producer ([python/ray_producer.py](./python/ray_producer.py))

- **Why**: Publishes a batch of typed tasks to RabbitMQ and collects results.
- **What**: Publishes `compute` and `slow` task messages, then polls `ray_results` until all results arrive.
- **How**: pika `basic_publish` with `delivery_mode=2` (persistent). `basic_get` polling loop for result collection.
