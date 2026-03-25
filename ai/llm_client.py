import json
import os
from typing import Any, Mapping, Sequence
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

ALLOWED_MOODS = {
    "neutral",
    "happy",
    "playful",
    "curious",
    "frustrated",
    "stressed",
    "sad",
    "angry",
    "anxious",
    "tired"
}
ALLOWED_INTENSITIES = {"low", "medium", "high"}
ALLOWED_INTENTS = {
    "asking_help",
    "venting",
    "joking",
    "chatting",
    "requesting_analysis",
    "unknown"
}
ALLOWED_REPLY_STYLES = {
    "direct_answer",
    "empathize_then_answer",
    "playful_answer",
    "calm_down_then_answer",
    "ask_clarifying_question"
}


def _normalize_choice(value: Any, allowed: set[str], fallback: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else fallback


def _normalize_free_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _fallback_mood_state(
    recent_messages: Sequence[str] | None = None
) -> dict[str, str]:
    recent_text = " | ".join(
        message.strip() for message in (recent_messages or []) if message.strip()
    )
    return {
        "mood": "neutral",
        "intensity": "low",
        "intent": "unknown",
        "confidence": "low",
        "reply_style": "direct_answer",
        "reasoning": "Not enough reliable signal from the latest message.",
        "recent_user_messages": recent_text
    }


def detect_mood(
    message: str,
    recent_messages: Sequence[str] | None = None
) -> dict[str, str]:
    latest_message = message.strip()
    recent_messages = [item.strip() for item in (recent_messages or []) if item.strip()]

    if not latest_message and not recent_messages:
        return _fallback_mood_state()

    prompt = "\n".join(
        [
            "Classify the user's likely mood from the latest message and recent messages.",
            "Treat mood as a hint, not a fact.",
            "Return JSON only with exactly these keys:",
            "mood, intensity, intent, confidence, reply_style, reasoning",
            "Allowed mood values: neutral, happy, playful, curious, frustrated, stressed, sad, angry, anxious, tired",
            "Allowed intensity values: low, medium, high",
            "Allowed intent values: asking_help, venting, joking, chatting, requesting_analysis, unknown",
            "Allowed reply_style values: direct_answer, empathize_then_answer, playful_answer, calm_down_then_answer, ask_clarifying_question",
            "Use low confidence if the signal is weak."
        ]
    )
    history_text = "\n".join(
        f"- {item}" for item in recent_messages[-5:]
    ) or "- none"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            f"Latest message: {latest_message or '[empty]'}",
                            "Recent messages:",
                            history_text
                        ]
                    )
                }
            ]
        )
        raw_content = response.choices[0].message.content or "{}"
        payload = json.loads(raw_content)
    except Exception as e:
        print("OpenAI mood detection error:", e)
        return _fallback_mood_state(recent_messages)

    mood_state = {
        "mood": _normalize_choice(payload.get("mood"), ALLOWED_MOODS, "neutral"),
        "intensity": _normalize_choice(
            payload.get("intensity"),
            ALLOWED_INTENSITIES,
            "low"
        ),
        "intent": _normalize_choice(payload.get("intent"), ALLOWED_INTENTS, "unknown"),
        "confidence": _normalize_choice(
            payload.get("confidence"),
            ALLOWED_INTENSITIES,
            "low"
        ),
        "reply_style": _normalize_choice(
            payload.get("reply_style"),
            ALLOWED_REPLY_STYLES,
            "direct_answer"
        ),
        "reasoning": _normalize_free_text(
            payload.get("reasoning"),
            "Signal is weak, so keep the tone gentle."
        ),
        "recent_user_messages": " | ".join(recent_messages[-5:])
    }
    return mood_state


def _build_discord_context(user_context: Mapping[str, Any] | None) -> str | None:
    if not user_context:
        return None

    lines = [
        "Discord user context:",
        f"- discord_user_id: {user_context.get('user_id', 'unknown')}",
        f"- discord_username: {user_context.get('username', 'unknown')}",
        f"- discord_display_name: {user_context.get('display_name', 'unknown')}",
        f"- discord_mention: {user_context.get('mention', 'unknown')}",
        f"- roast_nickname: {user_context.get('roast_nickname', '') or 'none'}",
        f"- roast_profile: {user_context.get('roast_profile', '') or 'none'}",
        f"- extra_instructions: {user_context.get('extra_instructions', '') or 'none'}",
        f"- detected_mood: {user_context.get('mood', 'neutral')}",
        f"- mood_intensity: {user_context.get('mood_intensity', 'low')}",
        f"- mood_intent: {user_context.get('mood_intent', 'unknown')}",
        f"- mood_confidence: {user_context.get('mood_confidence', 'low')}",
        f"- mood_reply_style: {user_context.get('mood_reply_style', 'direct_answer')}",
        f"- mood_reasoning: {user_context.get('mood_reasoning', '') or 'none'}",
        f"- recent_user_messages: {user_context.get('recent_user_messages', '') or 'none'}",
        f"- has_target: {user_context.get('has_target', 'false')}",
        f"- target_user_id: {user_context.get('target_user_id', '') or 'none'}",
        f"- target_username: {user_context.get('target_username', '') or 'none'}",
        f"- target_display_name: {user_context.get('target_display_name', '') or 'none'}",
        f"- target_mention: {user_context.get('target_mention', '') or 'none'}",
        f"- target_roast_nickname: {user_context.get('target_roast_nickname', '') or 'none'}",
        f"- target_roast_profile: {user_context.get('target_roast_profile', '') or 'none'}",
        f"- target_extra_instructions: {user_context.get('target_extra_instructions', '') or 'none'}",
        "Use this only to personalize the reply naturally and playfully.",
        "If has_target is true, direct the playful roast primarily at the target user instead of the requester.",
        "If target_roast_nickname or target_roast_profile is present, prioritize it for the target.",
        "If roast_nickname or roast_profile is present, prioritize it when teasing this user.",
        "Treat detected mood as a hint, not a certainty.",
        "If mood_confidence is low, do not overstate emotional assumptions.",
        "Match the opening tone to mood_reply_style before giving the main answer.",
        "Do not invent private information beyond these fields."
    ]
    return "\n".join(lines)

def _build_image_instruction(message: str) -> str:
    user_message = message.strip() or "Xem nhanh ảnh này rồi trả lời ngắn gọn."
    lines = [
        "Nhiệm vụ:",
        "- Khịa những thứ trong ảnh.",
        "- Trả lời ngắn gọn, đúng tone của nhân vật.",
        "- Không phân tích chuyên sâu, phân tích ngắn gọn.",
        "- Nếu user hỏi đoán nghề nghiệp, tập trung vào quần áo, dụng cụ và môi trường xung quanh để đưa ra phán đoán không đảm bảo",
        "- Nếu user hỏi 1 địa điểm trong ảnh, hãy tập trung phân tích ảnh và đưa ra phán đoán về địa điểm.",
        f"Yêu cầu của user: {user_message}"
    ]
    return "\n".join(lines)


def ask_ai(
    personality: str,
    message: str,
    user_context: Mapping[str, Any] | None = None
) -> str:
    """
    Chat with AI using text only
    """

    try:
        messages = [
            {
                "role": "system",
                "content": personality
            }
        ]
        discord_context = _build_discord_context(user_context)
        if discord_context:
            messages.append(
                {
                    "role": "system",
                    "content": discord_context
                }
            )
        messages.append(
            {
                "role": "user",
                "content": message
            }
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        print("OpenAI text error:", e)
        return "⚠️ AI text error."


def ask_ai_with_image(
    personality: str,
    message: str,
    image_url: str,
    user_context: Mapping[str, Any] | None = None
) -> str:
    """
    Chat with AI using text + image
    """

    try:
        messages = [
            {
                "role": "system",
                "content": personality
            }
        ]
        discord_context = _build_discord_context(user_context)
        if discord_context:
            messages.append(
                {
                    "role": "system",
                    "content": discord_context
                }
            )
        messages.append(
            {
                "role": "system",
                "content": _build_image_instruction(message)
            }
        )
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message.strip() or "Xem nhanh anh nay."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=250,
            temperature=0.6
        )

        return response.choices[0].message.content

    except Exception as e:
        print("OpenAI image error:", e)
        return "⚠️ AI image analysis error."
