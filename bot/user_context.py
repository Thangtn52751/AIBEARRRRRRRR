import json
from pathlib import Path
from typing import Any


USER_PROFILES_PATH = Path("data/user_profiles.json")


def load_user_profiles() -> dict[str, dict[str, str]]:
    if not USER_PROFILES_PATH.exists():
        return {}

    try:
        with USER_PROFILES_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    profiles: dict[str, dict[str, str]] = {}
    for user_id, profile in data.items():
        if isinstance(profile, dict):
            profiles[str(user_id)] = {
                key: str(value)
                for key, value in profile.items()
                if isinstance(key, str) and value is not None
            }
    return profiles


def build_user_context(
    author: Any,
    user_profiles: dict[str, dict[str, str]] | None = None
) -> dict[str, str]:
    profile = {}
    if user_profiles:
        profile = user_profiles.get(str(author.id), {})

    return {
        "user_id": str(author.id),
        "username": author.name,
        "display_name": getattr(author, "display_name", author.name),
        "mention": author.mention,
        "roast_nickname": profile.get("nickname", ""),
        "roast_profile": profile.get("roast_profile", ""),
        "extra_instructions": profile.get("extra_instructions", "")
    }


def build_message_context(
    author: Any,
    mentions: list[Any] | None = None,
    bot_user: Any | None = None,
    user_profiles: dict[str, dict[str, str]] | None = None
) -> dict[str, str]:
    context = build_user_context(author, user_profiles)
    mentions = mentions or []

    targets = [
        member for member in mentions
        if getattr(member, "id", None) != getattr(author, "id", None)
        and getattr(member, "id", None) != getattr(bot_user, "id", None)
        and not getattr(member, "bot", False)
    ]

    if not targets:
        return context

    target = targets[0]
    target_context = build_user_context(target, user_profiles)
    context.update(
        {
            "target_user_id": target_context["user_id"],
            "target_username": target_context["username"],
            "target_display_name": target_context["display_name"],
            "target_mention": target_context["mention"],
            "target_roast_nickname": target_context["roast_nickname"],
            "target_roast_profile": target_context["roast_profile"],
            "target_extra_instructions": target_context["extra_instructions"],
            "has_target": "true"
        }
    )
    return context
