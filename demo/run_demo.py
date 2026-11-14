#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Three-agent OSAP 0.1 demo: notes + calendar behind one supervisor.

The demo runs in process, but every step goes through the reference modules:
signed manifests and registration, capability-record discovery, a consent
receipt, two delegated tasks with attenuated budgets, a context handle, and an
audit chain with a redacted export. The task crosses two delegation
boundaries, so it covers the C7-01 precondition ("three Apps, at least two
delegation or handoff boundaries") and can be replayed by hand.

Run from anywhere:

    python3 demo/run_demo.py
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "impl"))

from osap import audit, capability, consent, context, crypto, identity, registry, task  # noqa: E402
from osap.clock import parse_timestamp  # noqa: E402

EXAMPLES = REPO / "examples"
NOW_TEXT = "2026-11-10T10:14:45Z"
NOW = parse_timestamp(NOW_TEXT)
TRACE = "trace_demo_01J9Z6Q3V8N2K4M7P1R5T0W"

SUPERVISOR = "agent://com.example.orchestrator/main#1a2b"
CALENDAR = "agent://com.example.calendar/agent#9c"
NOTES = "agent://com.example.notes/assistant#7f3a"
BUS = "agent://system/bus#0"
REGISTRY = "agent://system/registry#0"
USER = "user://local/example-user"

PARENT_TASK_ID = "task_01J9Z6Q3V8N2K4M7P1R5T0WXAB"
NOTES_TASK_ID = "task_01J9Z6Q3V8N2K4M7P1R5T0WXA1"
CALENDAR_TASK_ID = "task_01J9Z6Q3V8N2K4M7P1R5T0WXAE"
ROOT_TASK_ID = "task_01J9Z6Q3V8N2K4M7P1R5T0WXAA"

CAP_ID = "cap_demo_calendar_propose"
RECEIPT_ID = "consent_demo_calendar_propose"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def section(title: str) -> None:
    print()
    print(f"== {title} ==")


def require(condition: bool, message: str) -> None:
    """Fail the demo when a printed claim would be false."""

    if not condition:
        raise SystemExit(f"demo assertion failed: {message}")


def descriptor(uri: str, actions: list, resources: list, schemas: list, risk: str) -> dict:
    return {
        "cap": uri,
        "actions": actions,
        "resources": resources,
        "schemas": schemas,
        "risk": risk,
        "consent": "per_task" if risk in {"L3", "L4"} else "first_use",
    }


def build_manifest(app: str, agent: str, display: str, capabilities: list) -> tuple[dict, str]:
    private, public = crypto.generate_keypair()
    document = {
        "osap_manifest": "0.1",
        "app": app,
        "version": "1.0.0",
        "signature": "",
        "agents": [
            {
                "agent": agent,
                "display_name": display,
                "public_key": public,
                "capabilities": capabilities,
            }
        ],
    }
    return crypto.sign_document(document, private), public


def build_hello(agent: str, app: str, public: str, nonce: str) -> dict:
    return {
        "osap": "0.1",
        "id": f"msg_demo_hello_{nonce}",
        "type": "hello",
        "from": agent,
        "to": {"agent": BUS},
        "body": {
            "schema": "osap.hello/v1",
            "data": {
                "app": app,
                "agent": agent,
                "display_name": agent.rsplit("/", 1)[-1].split("#", 1)[0],
                "manifest_version": "1.0.0",
                "features": ["discover", "delegate", "consent", "context"],
                "encodings": ["json"],
                "public_key": public,
            },
        },
        "ts": NOW_TEXT,
    }


def event_chain(events: list) -> dict:
    """Link the recorded audit events into a verifiable chain (§10.5)."""

    previous = "sha256:0000000000000000"
    chained = []
    for index, event in enumerate(events, start=1):
        body = {
            "audit_id": f"audit_demo_{index:02d}",
            "trace_id": TRACE,
            "actor": event["actor"],
            "action": event["action"],
            "target": event["target"],
            "decision": event.get("decision", "allow"),
            "ts": NOW_TEXT,
            "prev_hash": previous,
        }
        for key in (
            "task_id",
            "session_id",
            "policy",
            "phase",
            "intent_ref",
            "consent_receipt_id",
            "context_refs",
        ):
            if key in event:
                body[key] = event[key]

        digest = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        body["hash"] = f"sha256:{digest}"
        previous = body["hash"]
        chained.append(body)

    return {
        "chain_id": "audit_chain_demo",
        "trace_id": TRACE,
        "created_at": NOW_TEXT,
        "events": chained,
    }


def main() -> int:
    print("OSAP 0.1 reference demo: notes + calendar behind one supervisor")
    print(f"simulated now: {NOW_TEXT}")

    # --- 1. signed manifests, trust, registration -------------------------
    section("1. manifests and registration (§4.1–§4.5, §7.1)")
    registry_instance = registry.Registry()

    setup = [
        (
            "app://com.example.orchestrator",
            SUPERVISOR,
            "Orchestrator",
            [
                descriptor(
                    "cap://os/tasks/orchestrate",
                    ["delegate", "cancel"],
                    ["task:*"],
                    ["osap.task/v1"],
                    "L1",
                )
            ],
        ),
        (
            "app://com.example.calendar",
            CALENDAR,
            "Calendar Agent",
            [
                descriptor(
                    "cap://os/calendar/events",
                    ["read", "propose", "create"],
                    ["calendar:primary"],
                    ["osap.calendar.event/v1", "osap.calendar.proposal/v1"],
                    "L3",
                )
            ],
        ),
        (
            "app://com.example.notes",
            NOTES,
            "Notes Assistant",
            [
                descriptor(
                    "cap://os/notes/documents",
                    ["read", "write"],
                    ["notes:local"],
                    ["osap.notes.document/v1", "osap.notes.summary/v1"],
                    "L2",
                )
            ],
        ),
    ]

    registrar = identity.Registrar(registry_instance)
    sessions = {}
    for index, (app, agent, display, capabilities) in enumerate(setup, start=1):
        manifest, public = build_manifest(app, agent, display, capabilities)
        registry_instance.trust(app, public)
        registry_instance.index_manifest(manifest)
        welcome = registrar.register(build_hello(agent, app, public, str(index)))
        sessions[agent] = welcome["session_id"]
        print(f"registered {agent} in {welcome['session_id']}")

    require(len(sessions) == 3, "all three agents must register")

    # --- 2. discovery ------------------------------------------------------
    section("2. capability discovery (§6.5, §6.6)")
    record = copy.deepcopy(load("capability-record.json"))
    record["agent"] = CALENDAR
    record["capability"]["actions"] = ["read", "propose", "create"]
    record["capability"]["schemas"] = [
        "osap.calendar.proposal/v1",
        "osap.calendar.event/v1",
    ]
    record["capability"]["risk"] = "L3"
    registry_instance.index_record(record, now=NOW)

    query = {
        "requires": ["calendar.propose"],
        "schemas": ["osap.calendar.proposal/v1"],
        "risk_max": "L3",
        "sources": ["vendor_registry"],
        "limit": 5,
    }
    candidates = registry_instance.discover(query, now=NOW)
    require(bool(candidates), "discovery must return the calendar record")
    candidate = candidates[0]
    print(f"found {candidate['agent']} via {candidate['source']['registry']}")
    print(f"match={candidate['match']} risk={candidate['risk']} hint={candidate['consent_hint']}")

    discover_message = {
        "id": "msg_demo_discover",
        "trace_id": TRACE,
        "type": "discover",
        "from": SUPERVISOR,
        "to": {"agent": REGISTRY},
    }

    # --- 3. consent and capability ----------------------------------------
    section("3. user consent and attenuated capability (§5.2–§5.8)")
    token = copy.deepcopy(load("capability.json"))
    token["cap_id"] = CAP_ID
    token["task_id"] = CALENDAR_TASK_ID
    token["root_task_id"] = ROOT_TASK_ID
    token["audience"] = CALENDAR
    token["subject"] = SUPERVISOR
    token["actions"] = ["propose"]
    token["constraints"]["max_depth"] = 2
    token["constraints"]["can_delegate"] = False
    token["iat"] = int(NOW.timestamp())
    token["nbf"] = int(NOW.timestamp())
    token["exp"] = int(NOW.timestamp()) + 3600

    receipt = copy.deepcopy(load("consent-receipt.json"))
    receipt["receipt_id"] = RECEIPT_ID
    receipt["cap_id"] = CAP_ID
    receipt["task_id"] = CALENDAR_TASK_ID
    receipt["audience"] = CALENDAR
    receipt["agent"] = SUPERVISOR
    receipt["actions"] = ["propose"]
    receipt["resources"] = ["calendar:primary"]
    receipt["risk"] = "L3"
    token["consent_receipt_id"] = RECEIPT_ID

    consent.validate(receipt, token, now=NOW)
    authority = capability.CapabilityAuthority(clock=lambda: NOW)
    authority.issue(token)
    authority.check_validity(token, now=NOW)
    authority.require_consent(token, risk="L3")
    print(f"receipt {RECEIPT_ID} covers {CAP_ID} for {CALENDAR}")
    print("L3 consent prerequisite satisfied; capability is valid at the simulated now")

    # --- 4. two delegations, two results ----------------------------------
    section("4. delegated tasks and results (§8.3–§8.8)")
    board = task.TaskBoard()
    parent = board.add(task.Task.from_document(load("task.json")))
    print(f"parent {parent.task_id} budget wall_ms={parent.budget['wall_ms']}")

    notes_delegate = copy.deepcopy(load("delegate.json"))
    notes_delegate["id"] = "msg_demo_delegate_notes"
    notes_delegate["trace_id"] = TRACE
    notes_delegate["causation_id"] = discover_message["id"]
    notes_delegate["to"] = {"agent": NOTES}
    notes_delegate["task"] = {
        "id": NOTES_TASK_ID,
        "parent": PARENT_TASK_ID,
        "root": ROOT_TASK_ID,
        "mode": "supervisor",
    }
    notes_delegate["auth"]["cap_id"] = "cap_demo_notes_summary"
    notes_delegate["body"]["data"].update(
        {
            "goal": "从本地笔记中提取会议背景与参会人",
            "budget": {"wall_ms": 3000, "tool_calls": 1, "depth": 2},
            "result_schema": "osap.notes.summary/v1",
        }
    )
    notes_cap = notes_delegate["body"]["data"]["delegated_capability"]
    notes_cap.update(
        {
            "cap_id": "cap_demo_notes_summary",
            "subject": NOTES,
            "audience": NOTES,
            "task_id": NOTES_TASK_ID,
            "root_task_id": ROOT_TASK_ID,
            "actions": ["read"],
            "resources": ["notes:local"],
            "parent_cap_id": "cap_demo_supervisor",
            "depth": 2,
        }
    )
    notes_cap["constraints"].update(
        {"max_budget": {"wall_ms": 3000, "tool_calls": 1}, "can_delegate": False}
    )

    notes_child = board.delegate(parent.task_id, notes_delegate)
    board.transition(notes_child, "accepted")
    board.transition(notes_child, "running")
    print(f"notes  {notes_child.task_id} budget wall_ms={notes_child.budget['wall_ms']}")

    notes_result = {
        "osap": "0.1",
        "id": "msg_demo_result_notes",
        "type": "result",
        "trace_id": TRACE,
        "causation_id": notes_delegate["id"],
        "session_id": sessions[SUPERVISOR],
        "from": NOTES,
        "to": {"agent": SUPERVISOR},
        "task": {"id": NOTES_TASK_ID, "status": "succeeded"},
        "body": {
            "schema": "osap.notes.summary/v1",
            "data": {
                "summary": "下周三上午只有 10:00-11:00 全员空闲",
                "context_ref": "obj://sha256:9f2c7b1a",
            },
        },
        "ts": NOW_TEXT,
    }
    board.accept_result(notes_result)
    print(f"notes  status={notes_child.status} schema={notes_result['body']['schema']}")

    calendar_delegate = copy.deepcopy(load("delegate.json"))
    calendar_delegate["id"] = "msg_demo_delegate_calendar"
    calendar_delegate["trace_id"] = TRACE
    calendar_delegate["causation_id"] = notes_result["id"]
    calendar_delegate["task"]["id"] = CALENDAR_TASK_ID
    calendar_delegate["task"]["parent"] = PARENT_TASK_ID
    calendar_delegate["task"]["root"] = ROOT_TASK_ID
    calendar_delegate["auth"]["cap_id"] = CAP_ID
    calendar_delegate["body"]["data"]["budget"] = {
        "wall_ms": 5000,
        "tool_calls": 2,
        "depth": 2,
    }

    calendar_child = board.delegate(parent.task_id, calendar_delegate)
    board.transition(calendar_child, "accepted")
    board.transition(calendar_child, "running")
    print(f"calendar {calendar_child.task_id} budget wall_ms={calendar_child.budget['wall_ms']}")

    calendar_result = copy.deepcopy(load("result.json"))
    calendar_result["id"] = "msg_demo_result_calendar"
    calendar_result["trace_id"] = TRACE
    calendar_result["causation_id"] = calendar_delegate["id"]
    calendar_result["task"]["id"] = calendar_child.task_id
    board.accept_result(calendar_result)
    print(
        f"calendar status={calendar_child.status} "
        f"slots={len(calendar_result['body']['data']['slots'])}"
    )

    board.transition(parent, "accepted")
    board.transition(parent, "running")
    board.transition(parent, "succeeded")
    print(f"parent {parent.task_id} status={parent.status}")
    require(len(board.children(parent.task_id)) == 2, "the task must cross two delegations")
    require(parent.status == "succeeded", "the parent task must succeed")

    trace_messages = [
        discover_message,
        notes_delegate,
        notes_result,
        calendar_delegate,
        calendar_result,
    ]

    # --- 5. context fabric -------------------------------------------------
    section("5. context resolution (§9.2–§9.4)")
    handle_document = copy.deepcopy(load("context-handle.json"))
    handle_document["handle"] = "ctx://user/memory/meeting_preferences"
    handle_document["scope"] = "user"
    handle_document["audience"] = CALENDAR
    handle_document["constraints"]["allowed_agents"] = [CALENDAR]
    fabric = context.ContextFabric()
    resolved = fabric.resolve(
        handle_document,
        agent=CALENDAR,
        granted_actions=["resolve", "memory.read"],
        now=NOW,
    )
    print(f"resolved {resolved['handle']} label={resolved['label']} scope={resolved['scope']}")
    print(f"audit decision={fabric.audit[-1]['decision']} action={fabric.audit[-1]['action']}")

    # --- 6. audit chain, redaction, recovery ------------------------------
    section("6. audit chain and redacted export (§10.5–§10.6, §8.11)")
    events = [
        {"actor": BUS, "action": "agent.registered", "target": SUPERVISOR},
        {"actor": BUS, "action": "agent.registered", "target": CALENDAR},
        {"actor": BUS, "action": "agent.registered", "target": NOTES},
        {"actor": SUPERVISOR, "action": "discovery.query", "target": REGISTRY},
        {
            "actor": USER,
            "action": "consent.granted",
            "target": CALENDAR,
            "consent_receipt_id": RECEIPT_ID,
        },
        {
            "actor": SUPERVISOR,
            "action": "task.created",
            "target": parent.task_id,
            "task_id": parent.task_id,
        },
        {
            "actor": SUPERVISOR,
            "action": "task.delegated",
            "target": notes_child.task_id,
            "task_id": notes_child.task_id,
            "session_id": sessions[SUPERVISOR],
        },
        {
            "actor": NOTES,
            "action": "task.completed",
            "target": notes_child.task_id,
            "task_id": notes_child.task_id,
        },
        {
            "actor": SUPERVISOR,
            "action": "task.delegated",
            "target": calendar_child.task_id,
            "task_id": calendar_child.task_id,
            "session_id": sessions[SUPERVISOR],
        },
        {
            "actor": CALENDAR,
            "action": "capability.exercised",
            "target": "calendar:primary",
            "policy": "calendar_per_task",
            "consent_receipt_id": RECEIPT_ID,
        },
        {
            "actor": CALENDAR,
            "action": "context.resolve",
            "target": resolved["handle"],
            "context_refs": ["obj://sha256:9f2c7b1a"],
        },
    ]

    intent_position = len(events) + 1
    events.append(
        {
            "actor": CALENDAR,
            "action": "effect.intent",
            "target": "calendar:primary",
            "phase": "intent",
            "policy": "calendar_per_task",
            "consent_receipt_id": RECEIPT_ID,
        }
    )
    events.append(
        {
            "actor": CALENDAR,
            "action": "effect.executed",
            "target": "calendar:primary",
            "phase": "outcome",
            "policy": "calendar_per_task",
            "consent_receipt_id": RECEIPT_ID,
            "intent_ref": f"audit_demo_{intent_position:02d}",
        }
    )
    events.append(
        {
            "actor": CALENDAR,
            "action": "task.completed",
            "target": calendar_child.task_id,
            "task_id": calendar_child.task_id,
        }
    )
    events.append(
        {
            "actor": SUPERVISOR,
            "action": "task.completed",
            "target": parent.task_id,
            "task_id": parent.task_id,
        }
    )

    chain = event_chain(events)
    audit.verify_chain(chain)
    print(f"verified {len(chain['events'])} events under {chain['trace_id']}")

    redacted = audit.redact_chain(chain, salt="demo-export-salt")
    require(redacted["chain_verified"], "the redacted export must stay verifiable")
    require(not redacted["plaintext_recoverable"], "redaction must not leave plaintext")
    print(
        "redacted export: "
        f"chain_verified={redacted['chain_verified']} "
        f"plaintext_recoverable={redacted['plaintext_recoverable']} "
        f"fields={redacted['redacted_fields']}"
    )

    recovery = audit.recover_effects(chain["events"])
    require(recovery["effect_state"] == "complete", "intent and outcome must reconcile")
    print(f"recovery: effect_state={recovery['effect_state']} alerted={recovery['alerted']}")

    trace = audit.trace_complete(trace_messages)
    require(trace["single_trace"], "every hop must share one trace_id")
    require(trace["complete"], "every hop after the first must carry causation_id")
    print(
        f"trace: single_trace={trace['single_trace']} "
        f"missing_causation={trace['missing_causation']} complete={trace['complete']}"
    )

    section("demo complete")
    print("registered=3 discovery=1 consent=1 delegated=2 context=1 audit=verified")
    print("trace=complete redaction=verified recovery=complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
