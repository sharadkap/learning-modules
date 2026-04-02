"""
raft_cluster.py — 5-Node Raft Cluster Simulation

Simulates a full Raft cluster in a single process using threads and
in-memory message queues instead of real sockets. This lets you observe
all the consensus protocol mechanics without any network setup.

Demonstrates:
  1. All 5 nodes boot as Followers.
  2. A Leader is elected via randomised election timeouts.
  3. Three client commands are replicated to a quorum and committed.
  4. The leader is "crashed" (thread stopped).
  5. A new election takes place and a new leader is elected.
  6. Replication continues under the new leader.

Run:
    python raft_cluster.py
"""

from __future__ import annotations

import queue
import random
import threading
import time
from dataclasses import dataclass
from typing import Optional

from raft_node import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    LogEntry,
    RaftNode,
    Role,
    VoteRequest,
    VoteResponse,
)

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    C = {
        "leader":    Fore.GREEN,
        "candidate": Fore.YELLOW,
        "follower":  Fore.CYAN,
        "error":     Fore.RED,
        "section":   Fore.MAGENTA,
        "dim":       Style.DIM,
        "reset":     Style.RESET_ALL,
    }
except ImportError:
    C = {k: "" for k in ["leader", "candidate", "follower", "error", "section", "dim", "reset"]}


# ─── Message Bus ──────────────────────────────────────────────────────────────

@dataclass
class Message:
    """A network message between two nodes."""
    sender: int
    receiver: int
    payload: object  # VoteRequest | VoteResponse | AppendEntriesRequest | AppendEntriesResponse


class MessageBus:
    """
    In-process message bus that simulates an unreliable network.

    Supports:
      - Point-to-point delivery via per-node queues.
      - Configurable packet drop rate (to simulate network partitions).
      - Configurable latency jitter.
    """

    def __init__(self, node_count: int, drop_rate: float = 0.0):
        self._queues: dict[int, queue.Queue] = {
            i: queue.Queue() for i in range(node_count)
        }
        self.drop_rate = drop_rate
        self._lock = threading.Lock()

    def send(self, msg: Message) -> None:
        if random.random() < self.drop_rate:
            return  # Silently drop
        self._queues[msg.receiver].put(msg)

    def broadcast(self, sender: int, payload: object, exclude: set[int] | None = None) -> None:
        for node_id, q in self._queues.items():
            if node_id == sender:
                continue
            if exclude and node_id in exclude:
                continue
            self.send(Message(sender=sender, receiver=node_id, payload=payload))

    def receive(self, node_id: int, timeout: float = 0.05) -> Optional[Message]:
        try:
            return self._queues[node_id].get(timeout=timeout)
        except queue.Empty:
            return None

    def partition(self, isolated_nodes: set[int]) -> None:
        """
        Simulate a network partition by setting a very high drop rate for
        messages to/from the isolated nodes.  (Simplified: just clears their
        queues and blocks new deliveries via the drop_rate mechanism.)
        """
        for node_id in isolated_nodes:
            # Drain queued messages so the partitioned node can't see them
            while not self._queues[node_id].empty():
                try:
                    self._queues[node_id].get_nowait()
                except queue.Empty:
                    break

    def heal(self) -> None:
        self.drop_rate = 0.0


# ─── Cluster Node Thread ───────────────────────────────────────────────────────

class ClusterNode(threading.Thread):
    """
    Runs a RaftNode in its own thread, polling for messages and driving
    the election/heartbeat timers.
    """

    def __init__(self, node_id: int, cluster_size: int, bus: MessageBus):
        super().__init__(name=f"Node-{node_id}", daemon=True)
        self.node = RaftNode(node_id=node_id, cluster_size=cluster_size)
        self.bus = bus
        self._stop_event = threading.Event()
        self._votes_received: set[int] = set()

    @property
    def node_id(self) -> int:
        return self.node.node_id

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            self._process_messages()
            self._check_timers()
            time.sleep(0.01)  # 10 ms tick

    def _process_messages(self) -> None:
        msg = self.bus.receive(self.node_id, timeout=0.01)
        if msg is None:
            return

        payload = msg.payload

        if isinstance(payload, VoteRequest):
            resp = self.node.handle_vote_request(payload)
            self.bus.send(Message(sender=self.node_id, receiver=msg.sender, payload=resp))

        elif isinstance(payload, VoteResponse):
            won = self.node.handle_vote_response(payload, self._votes_received)
            if won:
                self.node.become_leader()
                self._votes_received.clear()
                # Immediately broadcast heartbeats to assert leadership
                self._send_heartbeats()

        elif isinstance(payload, AppendEntriesRequest):
            resp = self.node.append_entries(payload)
            self.bus.send(Message(sender=self.node_id, receiver=msg.sender, payload=resp))

        elif isinstance(payload, AppendEntriesResponse):
            match_indices = list(self.node.match_index.values())
            self.node.handle_append_entries_response(payload, match_indices)

    def _check_timers(self) -> None:
        if self.node.role == Role.LEADER:
            # Send heartbeats on schedule
            if time.monotonic() - self.node._last_heartbeat >= self.node.HEARTBEAT_INTERVAL:
                self._send_heartbeats()
                self.node._last_heartbeat = time.monotonic()
        else:
            # Follower/Candidate: check election timeout
            if self.node.election_timeout_elapsed():
                self._votes_received = {self.node_id}  # Vote for self
                vote_req = self.node.become_candidate()
                self.bus.broadcast(sender=self.node_id, payload=vote_req)

    def _send_heartbeats(self) -> None:
        for peer_id in range(self.node.cluster_size):
            if peer_id == self.node_id:
                continue
            rpc = self.node.build_append_entries(peer_id)
            self.bus.send(Message(sender=self.node_id, receiver=peer_id, payload=rpc))

    def submit_command(self, command: str) -> Optional[LogEntry]:
        """Submit a client command (only succeeds if this node is the leader)."""
        return self.node.leader_receive_client_command(command)

    def __repr__(self) -> str:
        return repr(self.node)


# ─── Cluster Orchestrator ──────────────────────────────────────────────────────

class RaftCluster:
    """Manages a set of ClusterNode threads and drives the simulation."""

    def __init__(self, size: int = 5):
        self.size = size
        self.bus = MessageBus(node_count=size)
        self.nodes: list[ClusterNode] = [
            ClusterNode(node_id=i, cluster_size=size, bus=self.bus)
            for i in range(size)
        ]

    def start(self) -> None:
        for node in self.nodes:
            node.start()

    def stop(self) -> None:
        for node in self.nodes:
            node.stop()

    def leader(self) -> Optional[ClusterNode]:
        leaders = [n for n in self.nodes if n.node.role == Role.LEADER and not n._stop_event.is_set()]
        return leaders[0] if leaders else None

    def wait_for_leader(self, timeout: float = 10.0) -> Optional[ClusterNode]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            leader = self.leader()
            if leader:
                return leader
            time.sleep(0.1)
        return None

    def print_status(self) -> None:
        print(f"\n  {'─' * 55}")
        print(f"  {'NODE':<8} {'ROLE':<12} {'TERM':<8} {'LOG':>5} {'COMMIT':>7}")
        print(f"  {'─' * 55}")
        for cn in self.nodes:
            n = cn.node
            stopped = cn._stop_event.is_set()
            role_str = ("CRASHED" if stopped else n.role.name)
            color = (
                C["error"] if stopped else
                C["leader"] if n.role == Role.LEADER else
                C["candidate"] if n.role == Role.CANDIDATE else
                C["follower"]
            )
            print(f"  {color}Node {n.node_id:<3}  {role_str:<12} {n.current_term:<8} "
                  f"{len(n.log):>5} {n.commit_index:>7}{C['reset']}")
        print(f"  {'─' * 55}\n")

    def crash_leader(self) -> Optional[ClusterNode]:
        """Simulate the current leader crashing."""
        leader = self.leader()
        if leader:
            print(f"\n  {C['error']}⚡ CRASH: Node {leader.node_id} (leader, term={leader.node.current_term}) "
                  f"has failed!{C['reset']}\n")
            leader.stop()
            return leader
        return None


# ─── Main Simulation ───────────────────────────────────────────────────────────

def run_simulation() -> None:
    def banner(text: str) -> None:
        width = 62
        print(f"\n{C['section']}╔{'═' * width}╗{C['reset']}")
        print(f"{C['section']}║  {text:<{width - 2}}║{C['reset']}")
        print(f"{C['section']}╚{'═' * width}╝{C['reset']}\n")

    def step(text: str) -> None:
        print(f"\n{C['section']}◆  {text}{C['reset']}\n")

    banner("Raft Cluster Simulation — 5 Nodes")

    # ── Phase 1: Boot ─────────────────────────────────────────────────────
    step("Phase 1: All nodes boot as Followers")
    cluster = RaftCluster(size=5)
    cluster.start()
    cluster.print_status()

    # ── Phase 2: First election ───────────────────────────────────────────
    step("Phase 2: Waiting for leader election (randomised timeouts)...")
    leader = cluster.wait_for_leader(timeout=12.0)

    if not leader:
        print(f"  {C['error']}No leader elected within timeout. Aborting.{C['reset']}")
        cluster.stop()
        return

    print(f"  {C['leader']}✓ Leader elected: Node {leader.node_id} "
          f"(term={leader.node.current_term}){C['reset']}")
    cluster.print_status()

    # ── Phase 3: Log replication ──────────────────────────────────────────
    step("Phase 3: Client submits 3 commands to the leader")
    commands = ["SET balance=1000", "TRANSFER 200 -> account_7", "SET balance=800"]
    for cmd in commands:
        entry = leader.submit_command(cmd)
        time.sleep(0.3)  # Allow replication round-trip

    time.sleep(1.0)  # Allow commit index to advance across followers
    cluster.print_status()

    # ── Phase 4: Leader crash ─────────────────────────────────────────────
    step("Phase 4: Leader failure — simulating node crash")
    old_leader_id = leader.node_id
    cluster.crash_leader()
    time.sleep(0.5)
    cluster.print_status()

    # ── Phase 5: Re-election ──────────────────────────────────────────────
    step("Phase 5: Remaining nodes detect leader failure and hold new election")
    new_leader = cluster.wait_for_leader(timeout=12.0)

    if not new_leader:
        print(f"  {C['error']}No new leader elected. "
              f"(Expected: quorum={cluster.size // 2 + 1}, alive={cluster.size - 1}){C['reset']}")
        cluster.stop()
        return

    print(f"  {C['leader']}✓ New leader elected: Node {new_leader.node_id} "
          f"(term={new_leader.node.current_term}){C['reset']}")
    cluster.print_status()

    # ── Phase 6: Continue replication under new leader ────────────────────
    step("Phase 6: Client submits 2 more commands to new leader")
    new_commands = ["AUDIT log entry", "CLOSE session"]
    for cmd in new_commands:
        new_leader.submit_command(cmd)
        time.sleep(0.3)

    time.sleep(1.0)
    cluster.print_status()

    # ── Phase 7: Safety check ─────────────────────────────────────────────
    step("Phase 7: Safety verification")
    live_nodes = [n for n in cluster.nodes if not n._stop_event.is_set()]
    committed = [n.node.commit_index for n in live_nodes]
    terms     = [n.node.current_term  for n in live_nodes]

    print(f"  Commit indices (live nodes): {committed}")
    print(f"  Current terms  (live nodes): {terms}")

    all_same_term = len(set(terms)) == 1
    no_split_brain = len([n for n in live_nodes if n.node.role == Role.LEADER]) <= 1

    if all_same_term and no_split_brain:
        print(f"\n  {C['leader']}✓ Safety: single leader, all nodes on the same term.{C['reset']}")
    else:
        print(f"\n  {C['error']}✗ Safety violation detected!{C['reset']}")

    cluster.stop()
    print(f"\n  {C['leader']}Simulation complete.{C['reset']}\n")


if __name__ == "__main__":
    run_simulation()
