"""
raft_node.py — Single Raft Node State Machine

Demonstrates the core Raft state machine for a single node:
  - Three roles: Follower, Candidate, Leader
  - Election timeout and reset
  - Vote granting rules (term comparison + log freshness)
  - Log append and commit index advancement
  - Heartbeat emission (leader only)

Run:
    python raft_node.py
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ─── Data Structures ──────────────────────────────────────────────────────────

class Role(Enum):
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


@dataclass
class LogEntry:
    """A single entry in the Raft replicated log."""
    term: int
    index: int
    command: str

    def __repr__(self) -> str:
        return f"Entry(term={self.term}, idx={self.index}, cmd={self.command!r})"


@dataclass
class VoteRequest:
    """RequestVote RPC arguments."""
    candidate_id: int
    candidate_term: int
    last_log_index: int
    last_log_term: int


@dataclass
class VoteResponse:
    """RequestVote RPC reply."""
    voter_id: int
    term: int
    granted: bool


@dataclass
class AppendEntriesRequest:
    """AppendEntries RPC arguments (also used as heartbeat when entries=[])."""
    leader_id: int
    term: int
    prev_log_index: int
    prev_log_term: int
    entries: list[LogEntry]
    leader_commit: int


@dataclass
class AppendEntriesResponse:
    """AppendEntries RPC reply."""
    follower_id: int
    term: int
    success: bool
    match_index: int  # Highest log index the follower has matched


# ─── Raft Node ────────────────────────────────────────────────────────────────

class RaftNode:
    """
    A single Raft consensus node.

    Persistent state (survives restarts in production; initialised fresh here):
      current_term  — Latest term this node has seen
      voted_for     — Candidate this node voted for in current_term (or None)
      log           — Ordered list of LogEntry

    Volatile state:
      commit_index  — Highest log entry known to be committed
      last_applied  — Highest log entry applied to state machine

    Leader-only volatile state (reinitialised on each new election win):
      next_index    — For each follower: next log index to send them
      match_index   — For each follower: highest log index known to be replicated
    """

    ELECTION_TIMEOUT_MIN = 1.5   # seconds
    ELECTION_TIMEOUT_MAX = 3.0   # seconds
    HEARTBEAT_INTERVAL  = 0.5    # seconds

    def __init__(self, node_id: int, cluster_size: int = 5):
        self.node_id = node_id
        self.cluster_size = cluster_size
        self.quorum = (cluster_size // 2) + 1

        # Persistent state
        self.current_term: int = 0
        self.voted_for: Optional[int] = None
        self.log: list[LogEntry] = []

        # Volatile state
        self.commit_index: int = -1
        self.last_applied: int = -1
        self.role: Role = Role.FOLLOWER

        # Election timing
        self._reset_election_timeout()
        self._last_heartbeat = time.monotonic()

        # Leader-only state (populated when this node wins an election)
        self.next_index: dict[int, int] = {}
        self.match_index: dict[int, int] = {}

        print(f"  [Node {self.node_id}] Initialised as {self.role.name} — term={self.current_term}")

    # ── Timer helpers ──────────────────────────────────────────────────────

    def _reset_election_timeout(self) -> None:
        """Randomise the election timeout (Raft's key anti-collision mechanism)."""
        self._election_timeout = random.uniform(
            self.ELECTION_TIMEOUT_MIN,
            self.ELECTION_TIMEOUT_MAX,
        )
        self._election_deadline = time.monotonic() + self._election_timeout

    def election_timeout_elapsed(self) -> bool:
        return time.monotonic() >= self._election_deadline

    # ── Role transitions ───────────────────────────────────────────────────

    def become_candidate(self) -> VoteRequest:
        """
        Transition: Follower → Candidate.

        Steps per Raft paper §5.2:
          1. Increment current term.
          2. Vote for self.
          3. Reset election timer.
          4. Broadcast RequestVote RPCs.
        """
        self.current_term += 1
        self.voted_for = self.node_id
        self.role = Role.CANDIDATE
        self._reset_election_timeout()
        print(f"  [Node {self.node_id}] → CANDIDATE  (term={self.current_term})")

        return VoteRequest(
            candidate_id=self.node_id,
            candidate_term=self.current_term,
            last_log_index=len(self.log) - 1,
            last_log_term=self.log[-1].term if self.log else -1,
        )

    def become_leader(self) -> None:
        """
        Transition: Candidate → Leader.

        Reinitialise nextIndex and matchIndex for all peers.
        Immediately send an empty AppendEntries (heartbeat) to assert authority.
        """
        self.role = Role.LEADER
        for peer in range(self.cluster_size):
            if peer != self.node_id:
                self.next_index[peer] = len(self.log)
                self.match_index[peer] = -1
        print(f"  [Node {self.node_id}] → LEADER     (term={self.current_term}) ✓")

    def step_down(self, new_term: int) -> None:
        """
        Revert to Follower when we observe a higher term.

        Any node — follower, candidate, or leader — must immediately revert
        to follower if it sees a term greater than its own (§5.1).
        """
        print(f"  [Node {self.node_id}] → FOLLOWER   (term {self.current_term}→{new_term}, stepping down)")
        self.current_term = new_term
        self.voted_for = None
        self.role = Role.FOLLOWER
        self._reset_election_timeout()

    # ── Vote handling ──────────────────────────────────────────────────────

    def handle_vote_request(self, req: VoteRequest) -> VoteResponse:
        """
        Process a RequestVote RPC.

        Grant the vote only if ALL of the following hold (§5.2, §5.4):
          1. candidate_term >= current_term
          2. We haven't voted for someone else this term.
          3. The candidate's log is at least as up-to-date as ours
             (higher last log term, or equal term and at least as long a log).
        """
        # Rule 1: step down if we see a higher term
        if req.candidate_term > self.current_term:
            self.step_down(req.candidate_term)

        grant = False
        if req.candidate_term < self.current_term:
            # Stale candidate — decline
            pass
        elif self.voted_for in (None, req.candidate_id):
            # Check log freshness (§5.4.1)
            my_last_term  = self.log[-1].term if self.log else -1
            my_last_index = len(self.log) - 1
            log_ok = (
                req.last_log_term > my_last_term
                or (req.last_log_term == my_last_term and req.last_log_index >= my_last_index)
            )
            if log_ok:
                self.voted_for = req.candidate_id
                self._reset_election_timeout()
                grant = True

        result = "✓ granted" if grant else "✗ denied"
        print(f"  [Node {self.node_id}] Vote {result} → Node {req.candidate_id} "
              f"(term={req.candidate_term})")
        return VoteResponse(voter_id=self.node_id, term=self.current_term, granted=grant)

    def handle_vote_response(self, resp: VoteResponse, votes_received: set[int]) -> bool:
        """
        Tally an incoming VoteResponse.

        Returns True if this node just reached quorum and should become leader.
        """
        if resp.term > self.current_term:
            self.step_down(resp.term)
            return False

        if self.role != Role.CANDIDATE:
            return False

        if resp.granted:
            votes_received.add(resp.voter_id)
            print(f"  [Node {self.node_id}] Votes collected: {len(votes_received)}/{self.quorum} needed")
            if len(votes_received) >= self.quorum:
                return True

        return False

    # ── Log replication ────────────────────────────────────────────────────

    def append_entries(self, req: AppendEntriesRequest) -> AppendEntriesResponse:
        """
        Process an AppendEntries RPC (§5.3).

        Heartbeat:  req.entries == []  → just reset timer and update commit.
        Replication: req.entries != [] → validate consistency, append new entries.
        """
        # Reject stale leaders
        if req.term < self.current_term:
            return AppendEntriesResponse(
                follower_id=self.node_id,
                term=self.current_term,
                success=False,
                match_index=-1,
            )

        # Valid leader — reset election timeout, step down if needed
        if req.term > self.current_term:
            self.step_down(req.term)
        elif self.role == Role.CANDIDATE:
            # Another node won — become follower
            self.role = Role.FOLLOWER
            print(f"  [Node {self.node_id}] → FOLLOWER   (another leader elected, term={req.term})")

        self._reset_election_timeout()

        # Log consistency check (§5.3): does our log contain an entry at
        # prev_log_index whose term matches prev_log_term?
        if req.prev_log_index >= 0:
            if len(self.log) <= req.prev_log_index:
                # We're missing entries — tell leader to back up
                return AppendEntriesResponse(
                    follower_id=self.node_id,
                    term=self.current_term,
                    success=False,
                    match_index=len(self.log) - 1,
                )
            if self.log[req.prev_log_index].term != req.prev_log_term:
                # Conflict — delete this entry and everything after it
                self.log = self.log[:req.prev_log_index]
                return AppendEntriesResponse(
                    follower_id=self.node_id,
                    term=self.current_term,
                    success=False,
                    match_index=len(self.log) - 1,
                )

        # Append any new entries (dedup entries we already have)
        for entry in req.entries:
            if entry.index < len(self.log):
                if self.log[entry.index].term != entry.term:
                    self.log = self.log[:entry.index]  # Conflict — truncate
                    self.log.append(entry)
            else:
                self.log.append(entry)

        # Advance commit index
        if req.leader_commit > self.commit_index:
            self.commit_index = min(req.leader_commit, len(self.log) - 1)
            self._apply_committed_entries()

        return AppendEntriesResponse(
            follower_id=self.node_id,
            term=self.current_term,
            success=True,
            match_index=len(self.log) - 1,
        )

    def leader_receive_client_command(self, command: str) -> Optional[LogEntry]:
        """
        Accept a command from a client (leader-only, §5.3).

        Appends to the local log. The entry becomes committed once
        a quorum of followers acknowledge it via AppendEntries.
        """
        if self.role != Role.LEADER:
            print(f"  [Node {self.node_id}] Rejected client command — not the leader")
            return None

        entry = LogEntry(
            term=self.current_term,
            index=len(self.log),
            command=command,
        )
        self.log.append(entry)
        print(f"  [Node {self.node_id}] Appended to local log: {entry}")
        return entry

    def leader_advance_commit_index(self, match_indices: list[int]) -> None:
        """
        Advance commit_index to the highest N such that a quorum of nodes
        have match_index >= N and log[N].term == current_term (§5.3, §5.4).
        """
        if self.role != Role.LEADER:
            return

        # Include our own last log index
        all_indices = sorted(match_indices + [len(self.log) - 1], reverse=True)

        for n in all_indices:
            if n <= self.commit_index:
                break
            if n < len(self.log) and self.log[n].term == self.current_term:
                # Count how many nodes (including self) have this entry
                replicated = 1 + sum(1 for idx in match_indices if idx >= n)
                if replicated >= self.quorum:
                    print(f"  [Node {self.node_id}] Committed log index {n} "
                          f"(replicated on {replicated}/{self.cluster_size} nodes)")
                    self.commit_index = n
                    self._apply_committed_entries()
                    break

    def _apply_committed_entries(self) -> None:
        """Apply all committed but not yet applied entries to the state machine."""
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]
            print(f"  [Node {self.node_id}] Applied to state machine: {entry}")

    # ── Heartbeat emission ─────────────────────────────────────────────────

    def build_heartbeat(self, follower_id: int) -> AppendEntriesRequest:
        """Build an empty AppendEntries (heartbeat) for a given follower."""
        next_idx = self.next_index.get(follower_id, len(self.log))
        prev_idx = next_idx - 1
        prev_term = self.log[prev_idx].term if prev_idx >= 0 and self.log else -1

        return AppendEntriesRequest(
            leader_id=self.node_id,
            term=self.current_term,
            prev_log_index=prev_idx,
            prev_log_term=prev_term,
            entries=[],
            leader_commit=self.commit_index,
        )

    def build_append_entries(self, follower_id: int) -> AppendEntriesRequest:
        """Build an AppendEntries RPC with any unsent log entries for a follower."""
        next_idx = self.next_index.get(follower_id, 0)
        prev_idx = next_idx - 1
        prev_term = self.log[prev_idx].term if prev_idx >= 0 and self.log else -1
        entries = self.log[next_idx:]

        return AppendEntriesRequest(
            leader_id=self.node_id,
            term=self.current_term,
            prev_log_index=prev_idx,
            prev_log_term=prev_term,
            entries=entries,
            leader_commit=self.commit_index,
        )

    def handle_append_entries_response(
        self, resp: AppendEntriesResponse, match_indices: list[int]
    ) -> None:
        """Process a follower's AppendEntries response (leader-only)."""
        if resp.term > self.current_term:
            self.step_down(resp.term)
            return

        if resp.success:
            self.match_index[resp.follower_id] = resp.match_index
            self.next_index[resp.follower_id] = resp.match_index + 1
            match_indices[resp.follower_id] = resp.match_index
            self.leader_advance_commit_index(
                [v for k, v in self.match_index.items()]
            )
        else:
            # Back off: retry with one earlier entry
            self.next_index[resp.follower_id] = max(0, resp.match_index)

    def __repr__(self) -> str:
        return (
            f"RaftNode(id={self.node_id}, role={self.role.name}, "
            f"term={self.current_term}, log_len={len(self.log)}, "
            f"commit={self.commit_index})"
        )


# ─── Single-Node State Machine Demo ───────────────────────────────────────────

def demo_state_machine() -> None:
    """
    Walk through the state transitions a single Raft node goes through,
    without needing a real network.  Useful for understanding the rules
    in isolation before looking at the full cluster simulation.
    """
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        CYAN    = Fore.CYAN
        GREEN   = Fore.GREEN
        YELLOW  = Fore.YELLOW
        MAGENTA = Fore.MAGENTA
        RESET   = Style.RESET_ALL
    except ImportError:
        CYAN = GREEN = YELLOW = MAGENTA = RESET = ""

    def section(title: str) -> None:
        print(f"\n{CYAN}{'─' * 60}{RESET}")
        print(f"{CYAN}  {title}{RESET}")
        print(f"{CYAN}{'─' * 60}{RESET}")

    section("Phase 1: Node initialises as Follower")
    node = RaftNode(node_id=0, cluster_size=5)
    print(f"  State: {node}")

    section("Phase 2: Election timeout fires → node becomes Candidate")
    vote_req = node.become_candidate()
    print(f"  Broadcasting: {vote_req}")

    section("Phase 3: Node votes for itself and collects votes from quorum")
    votes: set[int] = {node.node_id}  # Self-vote
    # Simulate 2 more nodes granting their votes (quorum = 3 of 5)
    for peer_id in [1, 2]:
        fake_resp = VoteResponse(voter_id=peer_id, term=node.current_term, granted=True)
        won = node.handle_vote_response(fake_resp, votes)
        if won:
            node.become_leader()
            break

    section("Phase 4: Leader receives client commands and appends to log")
    commands = ["SET x=1", "SET y=2", "DELETE z"]
    for cmd in commands:
        node.leader_receive_client_command(cmd)

    section("Phase 5: Followers acknowledge — leader advances commit index")
    # Simulate 2 followers having replicated all 3 entries (indices 0, 1, 2)
    fake_match = {1: 2, 2: 2, 3: -1, 4: -1}
    node.match_index = fake_match
    node.leader_advance_commit_index(list(fake_match.values()))

    section("Phase 6: Leader sees higher term — steps down to Follower")
    node.step_down(new_term=5)
    print(f"  State: {node}")

    section("Phase 7: Node receives a vote request from a legitimate candidate")
    req = VoteRequest(
        candidate_id=3,
        candidate_term=5,
        last_log_index=5,
        last_log_term=5,
    )
    resp = node.handle_vote_request(req)
    print(f"  Response: {resp}")

    print(f"\n{GREEN}  ✓ Single-node state machine demo complete.{RESET}\n")


if __name__ == "__main__":
    demo_state_machine()
