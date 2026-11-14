# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Task tree, budgets, cancellation, results, and handoff (§8).

Scope is M2.5. The Bus keeps an in-memory task index:

- delegation creates a child node whose budget fits inside the parent
  remainder (§8.3, §8.5, §8.6);
- cancellation walks the tree downwards and skips detached children (§8.7);
- results are accepted only from the assignee and only with the declared
  `result_schema` (§8.8);
- handoff transfers ownership without creating a node, and a rejected or
  expired handoff leaves the task untouched (§8.9).

Two error codes carry the budget rules. Delegating a budget larger than the
parent's remainder is a policy refusal (`POLICY_DENIED`): the standard defines
no delegation-specific code. Exceeding a budget while executing is
`TASK_BUDGET_EXCEEDED` (§8.6).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import schema
from .capability import HIGH_RISK
from .errors import OsapError

TASK_SCHEMA = "task.schema.json"
DELEGATE_SCHEMA = "delegate.schema.json"
HANDOFF_SCHEMA = "handoff.schema.json"

STATUSES = (
    "created",
    "accepted",
    "running",
    "waiting_consent",
    "succeeded",
    "failed",
    "cancelled",
    "rejected",
)

#: States from which a task never moves again (§8.10).
TERMINAL = frozenset({"succeeded", "failed", "cancelled", "rejected"})

#: Legal transitions of the state machine in §8.10.
TRANSITIONS = {
    "created": frozenset({"accepted", "rejected", "cancelled"}),
    "accepted": frozenset({"running", "cancelled", "failed"}),
    "running": frozenset({"waiting_consent", "succeeded", "failed", "cancelled"}),
    "waiting_consent": frozenset({"running", "cancelled", "failed"}),
}

BUDGET_DIMENSIONS = ("wall_ms", "tool_calls", "tokens")


def check_budget(budget: dict, consumed: dict) -> None:
    """Raise `TASK_BUDGET_EXCEEDED` when `consumed` exceeds `budget` (§8.6)."""

    for dimension in BUDGET_DIMENSIONS:
        if dimension not in budget:
            continue
        used = consumed.get(dimension, 0)
        if used > budget[dimension]:
            raise OsapError(
                "TASK_BUDGET_EXCEEDED",
                f"{dimension} budget exceeded",
                details={
                    "dimension": dimension,
                    "budget": budget[dimension],
                    "consumed": used,
                },
            )

    if "money" in budget:
        limit = budget["money"]
        spent = consumed.get("money") or {}
        if spent:
            if spent.get("currency") != limit.get("currency"):
                raise OsapError(
                    "TASK_BUDGET_EXCEEDED",
                    "money budget currency mismatch",
                    details={"budget": limit, "consumed": spent},
                )
            if spent.get("amount", 0) > limit.get("amount", 0):
                raise OsapError(
                    "TASK_BUDGET_EXCEEDED",
                    "money budget exceeded",
                    details={"dimension": "money", "budget": limit, "consumed": spent},
                )


def remaining_budget(budget: dict, consumed: dict | None = None) -> dict:
    """Return the budget left in each dimension."""

    consumed = consumed or {}
    left: dict = {}
    for dimension in BUDGET_DIMENSIONS:
        if dimension in budget:
            left[dimension] = max(budget[dimension] - consumed.get(dimension, 0), 0)
    if "money" in budget:
        limit = budget["money"]
        spent = consumed.get("money") or {}
        left["money"] = {
            "currency": limit.get("currency"),
            "amount": max(limit.get("amount", 0) - spent.get("amount", 0), 0),
        }
    if "depth" in budget:
        left["depth"] = budget["depth"]
    return left


@dataclass
class Task:
    """One node of the task tree (§8.1)."""

    task_id: str
    root_task_id: str
    mode: str
    owner: str
    assignee: str
    budget: dict = field(default_factory=dict)
    status: str = "created"
    parent_task_id: str | None = None
    session_id: str | None = None
    result_schema: str | None = None
    authority: dict = field(default_factory=dict)
    consumed: dict = field(default_factory=dict)
    detached: bool = False

    @classmethod
    def from_document(cls, document: dict) -> "Task":
        """Build a task from a validated `task.schema.json` fixture."""

        schema.validate(TASK_SCHEMA, document)
        return cls(
            task_id=document["task_id"],
            root_task_id=document["root_task_id"],
            mode=document["mode"],
            owner=document["owner"],
            assignee=document["assignee"],
            budget=dict(document["budget"]),
            status=document["status"],
            parent_task_id=document.get("parent_task_id"),
            session_id=document.get("session_id"),
            result_schema=document.get("result_schema"),
            authority=dict(document.get("authority") or {}),
            detached=bool(document.get("detached", False)),
        )

    @classmethod
    def from_message(cls, message: dict) -> "Task":
        """Project a task from an envelope that carries no task record yet.

        Used by the handoff path, where the sender is the owner by definition.
        """

        task = message.get("task") or {}
        return cls(
            task_id=task["id"],
            root_task_id=task.get("root") or task["id"],
            mode=task.get("mode", "supervisor"),
            owner=message["from"],
            assignee=(message["body"].get("data") or {}).get("new_owner", message["from"]),
            parent_task_id=task.get("parent"),
            session_id=message.get("session_id"),
        )

    def snapshot(self) -> dict:
        return {
            "task_id": self.task_id,
            "owner": self.owner,
            "assignee": self.assignee,
            "status": self.status,
            "budget": dict(self.budget),
            "authority": dict(self.authority),
        }


class TaskBoard:
    """In-memory task tree, enough for delegation, cancel, result, and handoff."""

    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.audit: list[dict] = []

    # --- index -------------------------------------------------------------

    def add(self, task: Task) -> Task:
        self.tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    def require(self, task_id: str) -> Task:
        task = self.get(task_id)
        if task is None:
            raise OsapError("ROUTING_NOT_FOUND", f"unknown task: {task_id}")
        return task

    def children(self, task_id: str) -> list[Task]:
        return [task for task in self.tasks.values() if task.parent_task_id == task_id]

    # --- state machine -----------------------------------------------------

    def transition(self, task: Task, status: str) -> Task:
        """Apply one legal state transition, or refuse it (§8.10)."""

        if status not in STATUSES:
            raise OsapError("SCHEMA_INVALID", f"unknown task status: {status!r}")
        if status == task.status:
            return task
        if status not in TRANSITIONS.get(task.status, frozenset()):
            raise OsapError(
                "POLICY_DENIED",
                f"illegal task transition: {task.status} -> {status}",
                details={"from": task.status, "to": status},
            )
        self.audit.append(
            {"action": "task.status", "task_id": task.task_id, "from": task.status, "to": status}
        )
        task.status = status
        return task

    # --- cancellation ------------------------------------------------------

    def cancel(self, task_id: str) -> list[str]:
        """Cancel `task_id` and every non-detached descendant; return the ids."""

        root = self.require(task_id)
        cancelled: list[str] = []
        stack = [root]
        while stack:
            task = stack.pop()
            if task.detached:
                # Detached children keep running but lose the parent's authority (§8.7).
                continue
            if task.status not in TERMINAL:
                self.transition(task, "cancelled")
                cancelled.append(task.task_id)
            stack.extend(self.children(task.task_id))
        return cancelled

    # --- delegation --------------------------------------------------------

    def delegate(self, parent_id: str, message: dict) -> Task:
        """Create a child task from a `delegate` envelope (§8.5)."""

        data = message["body"]["data"]
        schema.validate(DELEGATE_SCHEMA, data)

        parent = self.require(parent_id)
        task = message.get("task") or {}
        if task.get("parent") != parent.task_id:
            raise OsapError(
                "POLICY_DENIED",
                "delegate task.parent is not the delegating task",
                details={"parent": parent.task_id, "message_parent": task.get("parent")},
            )
        if task["id"] in self.tasks:
            raise OsapError("DUPLICATE", f"task already exists: {task['id']}")

        requested = data["budget"]
        left = remaining_budget(parent.budget, parent.consumed)
        for dimension in BUDGET_DIMENSIONS:
            if dimension not in requested or dimension not in left:
                continue
            if requested[dimension] > left[dimension]:
                raise OsapError(
                    "POLICY_DENIED",
                    f"delegated {dimension} exceeds the parent remainder",
                    details={
                        "dimension": dimension,
                        "requested": requested[dimension],
                        "remaining": left[dimension],
                    },
                )
        if "depth" in requested and "depth" in parent.budget:
            if requested["depth"] != parent.budget["depth"] + 1:
                raise OsapError(
                    "POLICY_DENIED",
                    "delegated depth must be the parent depth plus one",
                    details={"requested": requested["depth"], "parent": parent.budget["depth"]},
                )

        child = Task(
            task_id=task["id"],
            root_task_id=task.get("root") or parent.root_task_id,
            mode=task.get("mode", parent.mode),
            owner=message["from"],
            assignee=(message.get("to") or {}).get("agent", parent.assignee),
            budget=dict(requested),
            status="created",
            parent_task_id=parent.task_id,
            session_id=message.get("session_id"),
            result_schema=data["result_schema"],
            authority={"cap_id": data["delegated_capability"]["cap_id"]},
        )
        self.add(child)
        self.audit.append(
            {
                "action": "task.delegated",
                "task_id": child.task_id,
                "parent": parent.task_id,
            }
        )
        return child

    # --- results -----------------------------------------------------------

    def accept_result(self, message: dict) -> Task:
        """Validate and apply a `result` message (§8.8)."""

        task = self.require(message["task"]["id"])
        if task.assignee != message["from"]:
            raise OsapError(
                "POLICY_DENIED",
                "only the assignee may return a result",
                details={"assignee": task.assignee, "sender": message["from"]},
            )
        claimed = message["body"]["schema"]
        if task.result_schema and claimed != task.result_schema:
            raise OsapError(
                "SCHEMA_INVALID",
                "result schema does not match the task contract",
                details={"expected": task.result_schema, "claimed": claimed},
            )
        status = (message.get("task") or {}).get("status")
        if status:
            self.transition(task, status)
        return task

    # --- handoff -----------------------------------------------------------

    def handoff(
        self,
        task: Task,
        message: dict,
        *,
        risk: str | None = None,
        renewed_consent: bool = False,
        accepted: bool = True,
    ) -> str:
        """Transfer ownership, or record a rejection without touching the task (§8.9)."""

        data = message["body"]["data"]
        schema.validate(HANDOFF_SCHEMA, data)

        if task.owner != message["from"]:
            raise OsapError(
                "POLICY_DENIED",
                "only the current owner may hand off a task",
                details={"owner": task.owner, "sender": message["from"]},
            )

        capability = data["delegated_capability"]
        new_owner = data["new_owner"]
        if data["task_id"] != task.task_id or capability["task_id"] != task.task_id:
            raise OsapError(
                "CAPABILITY_TASK_MISMATCH",
                "handoff capability is bound to a different task",
                details={"task_id": task.task_id},
            )
        if capability["audience"] != new_owner:
            raise OsapError(
                "CAPABILITY_AUDIENCE_MISMATCH",
                "handoff capability audience is not the new owner",
                details={"audience": capability["audience"], "new_owner": new_owner},
            )
        if capability["subject"] != new_owner:
            raise OsapError(
                "CAPABILITY_SUBJECT_MISMATCH",
                "handoff capability subject is not the new owner",
                details={"subject": capability["subject"], "new_owner": new_owner},
            )

        if risk in HIGH_RISK and (not renewed_consent or not capability.get("consent_receipt_id")):
            raise OsapError(
                "POLICY_CONSENT_REQUIRED",
                f"{risk} handoff requires a fresh consent receipt for the new owner",
                details={"risk": risk, "new_owner": new_owner},
            )

        if not accepted:
            self.audit.append(
                {
                    "action": "task.handoff",
                    "task_id": task.task_id,
                    "result": "rejected",
                    "owner": task.owner,
                }
            )
            return "rejected"

        previous = task.owner
        task.owner = new_owner
        task.assignee = new_owner
        task.authority = {"cap_id": capability["cap_id"]}
        self.audit.append(
            {
                "action": "task.handoff",
                "task_id": task.task_id,
                "result": "accepted",
                "from": previous,
                "to": new_owner,
                "cap_id": capability["cap_id"],
            }
        )
        return "accepted"

    # --- ownership ---------------------------------------------------------

    def require_owner(self, task_id: str, sender: str) -> Task:
        """Refuse control commands from anyone but the current owner (§8.9)."""

        task = self.require(task_id)
        if task.owner != sender:
            raise OsapError(
                "POLICY_DENIED",
                "sender no longer owns the task",
                details={"owner": task.owner, "sender": sender},
            )
        return task
