import json
from pathlib import Path
from typing import Any


USER_PROFILES_PATH = Path("data/user_profiles.json")
GUILD_BIRTHDAY_SETTINGS_PATH = Path("data/guild_birthday_settings.json")


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def _save_json_object(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    temp_path.replace(path)


def load_user_profiles() -> dict[str, dict[str, str]]:
    data = _load_json_object(USER_PROFILES_PATH)
    profiles: dict[str, dict[str, str]] = {}
    for user_id, profile in data.items():
        if isinstance(profile, dict):
            profiles[str(user_id)] = {
                key: str(value)
                for key, value in profile.items()
                if isinstance(key, str) and value is not None
            }
    return profiles


def save_user_profiles(user_profiles: dict[str, dict[str, str]]) -> None:
    sanitized_profiles: dict[str, dict[str, str]] = {}
    for user_id, profile in user_profiles.items():
        if not isinstance(profile, dict):
            continue

        sanitized_profiles[str(user_id)] = {
            str(key): str(value)
            for key, value in profile.items()
            if isinstance(key, str) and value is not None
        }

    _save_json_object(USER_PROFILES_PATH, sanitized_profiles)


def load_guild_birthday_settings() -> dict[str, dict[str, Any]]:
    data = _load_json_object(GUILD_BIRTHDAY_SETTINGS_PATH)
    settings: dict[str, dict[str, Any]] = {}

    for guild_id, raw_setting in data.items():
        if not isinstance(raw_setting, dict):
            continue

        birthday_channel_id = raw_setting.get("birthday_channel_id")
        raw_last_announced = raw_setting.get("last_announced", {})
        last_announced: dict[str, str] = {}

        if isinstance(raw_last_announced, dict):
            last_announced = {
                str(user_id): str(date_string)
                for user_id, date_string in raw_last_announced.items()
                if date_string is not None
            }

        settings[str(guild_id)] = {
            "birthday_channel_id": str(birthday_channel_id) if birthday_channel_id is not None else "",
            "last_announced": last_announced
        }

    return settings


def save_guild_birthday_settings(settings: dict[str, dict[str, Any]]) -> None:
    sanitized_settings: dict[str, dict[str, Any]] = {}

    for guild_id, raw_setting in settings.items():
        if not isinstance(raw_setting, dict):
            continue

        birthday_channel_id = raw_setting.get("birthday_channel_id")
        raw_last_announced = raw_setting.get("last_announced", {})
        last_announced: dict[str, str] = {}

        if isinstance(raw_last_announced, dict):
            last_announced = {
                str(user_id): str(date_string)
                for user_id, date_string in raw_last_announced.items()
                if date_string is not None
            }

        sanitized_settings[str(guild_id)] = {
            "birthday_channel_id": (
                str(birthday_channel_id)
                if birthday_channel_id not in (None, "")
                else ""
            ),
            "last_announced": last_announced
        }

    _save_json_object(GUILD_BIRTHDAY_SETTINGS_PATH, sanitized_settings)


def build_user_context(
    author: Any,
    user_profiles: dict[str, dict[str, str]] | None = None,
    runtime_state: dict[str, str] | None = None
) -> dict[str, str]:
    profile = {}
    if user_profiles:
        profile = user_profiles.get(str(author.id), {})
    runtime_state = runtime_state or {}

    return {
        "user_id": str(author.id),
        "username": author.name,
        "display_name": getattr(author, "display_name", author.name),
        "mention": author.mention,
        "roast_nickname": profile.get("nickname", ""),
        "roast_profile": profile.get("roast_profile", ""),
        "extra_instructions": profile.get("extra_instructions", ""),
        "mood": runtime_state.get("mood", "neutral"),
        "mood_intensity": runtime_state.get("intensity", "low"),
        "mood_intent": runtime_state.get("intent", "unknown"),
        "mood_confidence": runtime_state.get("confidence", "low"),
        "mood_reply_style": runtime_state.get("reply_style", "direct_answer"),
        "mood_reasoning": runtime_state.get("reasoning", ""),
        "recent_user_messages": runtime_state.get("recent_user_messages", "")
    }


def build_message_context(
    author: Any,
    mentions: list[Any] | None = None,
    bot_user: Any | None = None,
    user_profiles: dict[str, dict[str, str]] | None = None,
    runtime_state: dict[str, str] | None = None
) -> dict[str, str]:
    context = build_user_context(author, user_profiles, runtime_state)
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
