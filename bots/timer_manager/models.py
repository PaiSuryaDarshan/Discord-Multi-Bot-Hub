"""Data models used by Timer Manager."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class TimerStatus(StrEnum):
    """Possible timer states."""

    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Timer:
    """Represent a Discord timer."""

    timer_id: str
    creator_id: int
    notify_user_ids: tuple[int, ...]
    notify_role_ids: tuple[int, ...]
    channel_id: int
    label: str
    duration_seconds: int

    status: TimerStatus = TimerStatus.RUNNING
    message_id: int | None = None
    end_time: datetime | None = None
    remaining_seconds: int | None = None

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("Timer duration must be greater than zero.")

        if self.remaining_seconds is None:
            self.remaining_seconds = self.duration_seconds

    def get_remaining_seconds(self) -> int:
        """Return the timer's current remaining duration."""

        if self.status == TimerStatus.RUNNING and self.end_time is not None:
            now = datetime.now(timezone.utc)
            remaining = int((self.end_time - now).total_seconds())
            return max(0, remaining)

        return max(0, self.remaining_seconds or 0)

    def is_finished(self) -> bool:
        """Return whether the running timer has reached zero."""

        return (
            self.status == TimerStatus.RUNNING
            and self.get_remaining_seconds() <= 0
        )
