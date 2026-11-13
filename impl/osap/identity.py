# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OSAP Authors
"""Agent registration and reserved namespaces (standard.md §4.1–§4.7).

`Registrar` models the Bus side of `hello` handling. The Bus is the naming
authority: an agent may not claim an app it does not belong to, may not claim
a reserved namespace, and must prove that its public key is bound to the app
manifest before a `welcome` is returned.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from . import envelope
from .errors import OsapError

#: Namespaces reserved for the system (§4.4). Third parties MUST NOT register.
RESERVED_PREFIXES = (
    "agent://system/",
    "cap://os/",
    "ctx://os/",
    "event://os/",
)


def is_reserved(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in RESERVED_PREFIXES)


def app_of_agent(agent: str) -> str:
    """Map `agent://com.example.notes/assistant#7f3a` to `app://com.example.notes`."""

    if not agent.startswith("agent://"):
        raise OsapError("AUTH_DENIED", f"not an agent name: {agent!r}")
    authority = agent[len("agent://") :].split("/", 1)[0].split("#", 1)[0]
    if not authority:
        raise OsapError("AUTH_DENIED", f"agent name has no authority: {agent!r}")
    return f"app://{authority}"


@dataclass(frozen=True)
class Registration:
    agent: str
    app: str
    public_key: str
    session_id: str
    manifest_version: str


class Registrar:
    """Validates `hello` and issues `welcome` for one registry."""

    def __init__(self, registry) -> None:
        self.registry = registry
        self.registrations: dict[str, Registration] = {}

    def register(self, hello: dict) -> dict:
        envelope.validate(hello)
        if hello.get("type") != "hello":
            raise OsapError("SCHEMA_INVALID", "registration requires a hello message")

        data = hello["body"]["data"]
        agent = data.get("agent")
        app = data.get("app")
        public_key = data.get("public_key")
        for field, value in (("agent", agent), ("app", app), ("public_key", public_key)):
            if not isinstance(value, str) or not value:
                raise OsapError("SCHEMA_INVALID", f"hello.body.data.{field} is required")

        if hello.get("from") != agent:
            raise OsapError("AUTH_DENIED", "hello.from does not match the claimed agent")

        if is_reserved(agent):
            raise OsapError("AUTH_DENIED", "reserved namespace cannot be registered by a third party")

        if app_of_agent(agent) != app:
            raise OsapError("AUTH_DENIED", "agent does not belong to the claimed app")

        manifest = self.registry.manifest_for(app)
        if manifest is None:
            raise OsapError("AUTH_DENIED", "app is not registered")

        self.registry.require_manifest_signature(manifest)

        entry = self.registry.agent_entry(agent)
        if entry is None:
            raise OsapError("AUTH_DENIED", "agent is not listed in the app manifest")
        if entry["public_key"] != public_key:
            raise OsapError("AUTH_DENIED", "public key is not bound to the app identity")

        if not self.registry.key_usable(agent):
            raise OsapError("AUTH_DENIED", "rotated key is outside the grace period")

        registration = Registration(
            agent=agent,
            app=app,
            public_key=public_key,
            session_id=f"session_{secrets.token_hex(8)}",
            manifest_version=entry.get("manifest_version", manifest.get("version", "")),
        )
        self.registrations[agent] = registration
        return self._welcome(hello, registration)

    def _welcome(self, hello: dict, registration: Registration) -> dict:
        welcome = {
            "osap": hello["osap"],
            "id": f"welcome_{hello['id']}",
            "type": "welcome",
            "causation_id": hello["id"],
            "session_id": registration.session_id,
            "from": "agent://system/bus#0",
            "to": {"agent": registration.agent},
            "body": {
                "schema": "osap.welcome/v1",
                "data": {
                    "osap": hello["osap"],
                    "session_id": registration.session_id,
                    "app": registration.app,
                    "features": ["discover", "delegate", "consent", "context"],
                    "limits": {"max_frame_bytes": 8 * 1024 * 1024},
                },
            },
            "ts": hello.get("ts"),
        }
        return welcome
