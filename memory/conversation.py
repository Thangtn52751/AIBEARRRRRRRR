from typing import Any


class ConversationMemory:
    def __init__(self, max_messages: int = 20):
        self.history: dict[str, list[dict[str, str]]] = {}
        self.max_messages = max_messages

    def get(self, user_id: Any) -> list[dict[str, str]]:
        return self.history.get(str(user_id), [])

    def add(self, user_id: Any, role: str, content: str) -> None:
        user_key = str(user_id)

        if user_key not in self.history:
            self.history[user_key] = []

        self.history[user_key].append(
            {
                "role": str(role),
                "content": str(content)
            }
        )
        self.history[user_key] = self.history[user_key][-self.max_messages:]

    def get_recent_user_messages(self, user_id: Any, limit: int = 5) -> list[str]:
        history = self.get(user_id)
        messages = [
            item["content"]
            for item in history
            if item.get("role") == "user" and item.get("content")
        ]
        return messages[-limit:]
