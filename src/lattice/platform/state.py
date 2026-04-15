from __future__ import annotations

from lattice.platform.specs import RunStatus


ALLOWED_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    "prepared": {"running", "failed"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


def can_transition(current: RunStatus, target: RunStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
