from __future__ import annotations

import uuid
from typing import NamedTuple


class RegistrationData(NamedTuple):
    username: str
    password: str
    real_name: str
    phone: str
    mail: str


def build_registration_data(*, username: str | None = None) -> RegistrationData:
    """Build one valid, unique registration payload that fits current UI limits."""
    token = uuid.uuid4().hex
    generated_username = username or f"ui{token[:9]}"
    phone_number = int(token[9:17], 16) % 100_000_000
    phone = f"139{phone_number:08d}"
    mail_local = generated_username if username is None else f"ui{token[:9]}"
    return RegistrationData(
        username=generated_username,
        password="UiTest123!",
        real_name="UI自动化",
        phone=phone,
        mail=f"{mail_local}@test.com",
    )


class GroupData:
    """Mutable UI-owned group resource used to track cleanup after rename/delete."""

    def __init__(self, name: str, active: bool = True):
        self.name = name
        self.active = active


def build_group_data(*, prefix: str = "ui-g") -> GroupData:
    """Build one short unique group name suitable for repeated UI lifecycle tests."""
    token = uuid.uuid4().hex[:8]
    normalized_prefix = prefix.rstrip("-")
    return GroupData(name=f"{normalized_prefix}-{token}")


class LinkData:
    """Mutable UI-owned short-link resource tracked across edit and cleanup actions."""

    def __init__(self, origin_url: str, description: str, active: bool = True):
        self.origin_url = origin_url
        self.description = description
        self.active = active


def build_link_data(*, target_url: str | None = None, prefix: str = "ui-link") -> LinkData:
    """Build a unique valid short-link target and description for repeatable UI tests."""
    from config import TARGET_URL

    token = uuid.uuid4().hex[:8]
    origin_url = (target_url or TARGET_URL).strip()
    normalized_prefix = prefix.rstrip("-")
    return LinkData(origin_url=origin_url, description=f"{normalized_prefix}-{token}")


def build_profile_mail() -> str:
    """Build one unique valid e-mail for reversible account-profile UI checks."""
    return f"ui-profile-{uuid.uuid4().hex[:8]}@test.com"
