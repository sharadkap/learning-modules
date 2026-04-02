"""
ray_basics.py — Core Ray concepts on a local cluster.

Demonstrates:
    1. Remote functions and object references
    2. Parallel fan-out and speedup
    3. Actors — stateful remote objects
    4. ray.wait() for non-blocking progress tracking
    5. Dependent task pipelines

Does NOT require RabbitMQ. Runs standalone.

Run (from ray_learnings/python/):
    python ray_basics.py
"""

import time
import ray

ray.init(num_cpus=4, ignore_reinit_error=True)

SEP = "─" * 60


def section(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


# ── Remote Functions ───────────────────────────────────────────────────────────

@ray.remote
def add(x: int, y: int) -> int:
    """Remote addition — executes in a Ray worker process."""
    return x + y


@ray.remote
def cpu_bound(n: int) -> int:
    """Simulates CPU-intensive work: sum of squares."""
    return sum(i * i for i in range(n))


@ray.remote
def slow_task(job_id: str, duration: float = 0.5) -> dict:
    """Simulates a slow external call."""
    time.sleep(duration)
    return {"job_id": job_id, "status": "done", "duration": duration}


# ── Stateful Actor ─────────────────────────────────────────────────────────────

@ray.remote
class Counter:
    """
    A stateful Ray actor.
    Actors run in their own process and serialise concurrent method calls.
    Use actors for shared mutable state across distributed workers.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.count = 0

    def increment(self, by: int = 1) -> int:
        self.count += by
        return self.count

    def reset(self) -> None:
        self.count = 0

    def value(self) -> int:
        return self.count


# ── Demos ──────────────────────────────────────────────────────────────────────

def demo_basic_remote() -> None:
    section("1. Basic Remote Function")
    # .remote() dispatches immediately, returns an ObjectRef (future)
    ref = add.remote(10, 20)
    result = ray.get(ref)           # blocks until result is available
    print(f"add.remote(10, 20) = {result}")

    # Multiple concurrent calls
    refs = [add.remote(i, i) for i in range(5)]
    results = ray.get(refs)         # waits for all
    print(f"add.remote(i, i) for i in 0..4 = {results}")


def demo_parallel_speedup() -> None:
    section("2. Parallel Speedup")
    n = 2_000_000
    t0 = time.perf_counter()
    refs = [cpu_bound.remote(n) for _ in range(4)]
    ray.get(refs)
    elapsed = time.perf_counter() - t0
    print(f"4 × cpu_bound({n:,}) in parallel: {elapsed:.2f}s")


def demo_actor() -> None:
    section("3. Actor — Stateful Remote Object")
    counter = Counter.remote("demo-counter")

    # All calls return ObjectRefs immediately (non-blocking)
    increment_refs = [counter.increment.remote(i) for i in range(1, 6)]
    values = ray.get(increment_refs)
    print(f"Increments: {values}")          # [1, 3, 6, 10, 15]

    total = ray.get(counter.value.remote())
    print(f"Total: {total}")                # 15

    ray.get(counter.reset.remote())
    print(f"After reset: {ray.get(counter.value.remote())}")  # 0


def demo_ray_wait() -> None:
    section("4. ray.wait() — Process Results as They Arrive")
    durations = [0.1, 0.4, 0.2, 0.6, 0.3]
    refs = [slow_task.remote(f"job-{i}", d) for i, d in enumerate(durations)]

    remaining = refs[:]
    completed = 0
    while remaining:
        done, remaining = ray.wait(remaining, num_returns=1, timeout=2.0)
        for ref in done:
            result = ray.get(ref)
            completed += 1
            print(f"  [{completed}/5] {result}")


def demo_pipeline() -> None:
    section("5. Dependent Pipeline")
    # add(3, 4) → cpu_bound(result) → slow_task(str(result))
    ref1 = add.remote(3, 4)               # 7
    val1 = ray.get(ref1)
    ref2 = cpu_bound.remote(val1)
    val2 = ray.get(ref2)
    ref3 = slow_task.remote(f"pipe-{val2}", duration=0.1)
    final = ray.get(ref3)
    print(f"Pipeline: add(3,4)→cpu_bound→slow_task = {final}")


if __name__ == "__main__":
    print("Ray Basics — local cluster (4 CPUs)")
    print("Dashboard: http://127.0.0.1:8265 (if enabled)\n")

    demo_basic_remote()
    demo_parallel_speedup()
    demo_actor()
    demo_ray_wait()
    demo_pipeline()

    print(f"\n{SEP}\n  All demos complete.\n{SEP}")
    ray.shutdown()
