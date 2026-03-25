from contextlib import closing
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_BIRTHDAY_DB_PATH = DATA_DIR / "birthdays.db"


class BirthdayStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_BIRTHDAY_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_birthdays (
                    user_id TEXT PRIMARY KEY,
                    day INTEGER NOT NULL,
                    month INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_birthdays_month_day
                ON user_birthdays (month, day)
                """
            )
            connection.commit()

    @staticmethod
    def _parse_birthday(value: str) -> tuple[int, int] | None:
        if not isinstance(value, str):
            return None

        parts = value.split("/")
        if len(parts) != 2:
            return None

        try:
            day = int(parts[0])
            month = int(parts[1])
        except ValueError:
            return None

        if not (1 <= day <= 31 and 1 <= month <= 12):
            return None

        return day, month

    @staticmethod
    def _format_birthday(day: int, month: int) -> str:
        return f"{day:02d}/{month:02d}"

    def set_birthday(self, user_id: int | str, day: int, month: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO user_birthdays (user_id, day, month)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    day = excluded.day,
                    month = excluded.month
                """,
                (str(user_id), day, month)
            )
            connection.commit()

    def get_birthday(self, user_id: int | str) -> str | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT day, month FROM user_birthdays WHERE user_id = ?",
                (str(user_id),)
            ).fetchone()

        if row is None:
            return None

        day, month = row
        return self._format_birthday(day, month)

    def delete_birthday(self, user_id: int | str) -> bool:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                "DELETE FROM user_birthdays WHERE user_id = ?",
                (str(user_id),)
            )
            connection.commit()
            return cursor.rowcount > 0

    def get_users_by_birthday(self, day: int, month: int) -> list[str]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT user_id
                FROM user_birthdays
                WHERE day = ? AND month = ?
                """,
                (day, month)
            ).fetchall()

        return [str(user_id) for user_id, in rows]

    def migrate_from_profiles(self, user_profiles: dict[str, dict[str, str]]) -> bool:
        profiles_updated = False

        for user_id, profile in user_profiles.items():
            if not isinstance(profile, dict):
                continue

            birthday_value = profile.get("birthday")
            parsed_birthday = self._parse_birthday(birthday_value) if birthday_value else None
            if parsed_birthday is None:
                continue

            day, month = parsed_birthday
            self.set_birthday(user_id, day, month)
            profile.pop("birthday", None)
            profiles_updated = True

        return profiles_updated
