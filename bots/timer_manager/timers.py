"""Core timer-management logic."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .models import PomodoroPhase, PomodoroState, Timer, TimerStatus


class TimerNotFoundError(KeyError):
    """Raised when a timer ID does not exist."""


class TimerPermissionError(PermissionError):
    """Raised when a user cannot control a timer."""


class InvalidTimerStateError(ValueError):
    """Raised when an action is invalid for the timer's current state."""


class TimerManager:
    """Create and manage timers independently of Discord."""

    def __init__(self) -> None:
        self._timers: dict[str, Timer] = {}

    def create_timer(
        self,
        *,
        creator_id: int,
        notify_user_ids: tuple[int, ...],
        notify_role_ids: tuple[int, ...],
        channel_id: int,
        duration_seconds: int,
        label: str = "Timer",
    ) -> Timer:
        """Create and start a new timer."""

        if duration_seconds <= 0:
            raise ValueError("Timer duration must be greater than zero.")

        timer_id = uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        timer = Timer(
            timer_id=timer_id,
            creator_id=creator_id,
            notify_user_ids=notify_user_ids,
            notify_role_ids=notify_role_ids,
            channel_id=channel_id,
            label=label.strip() or "Timer",
            duration_seconds=duration_seconds,
            remaining_seconds=duration_seconds,
            end_time=now + timedelta(seconds=duration_seconds),
        )

        self._timers[timer_id] = timer
        return timer

    def create_pomodoro(
        self,
        *,
        creator_id: int,
        notify_user_id: int,
        channel_id: int,
        focus_seconds: int = 1_500,
        short_break_seconds: int = 300,
        long_break_seconds: int = 900,
        sessions: int = 4,
    ) -> Timer:
        """Create a Pomodoro beginning with its first focus phase."""

        if min(focus_seconds, short_break_seconds, long_break_seconds) <= 0:
            raise ValueError("Pomodoro durations must be greater than zero.")
        if sessions <= 0:
            raise ValueError("Pomodoro sessions must be greater than zero.")

        timer = self.create_timer(
            creator_id=creator_id,
            notify_user_ids=(notify_user_id,),
            notify_role_ids=(),
            channel_id=channel_id,
            duration_seconds=focus_seconds,
            label="Pomodoro",
        )
        timer.pomodoro = PomodoroState(
            focus_seconds=focus_seconds,
            short_break_seconds=short_break_seconds,
            long_break_seconds=long_break_seconds,
            total_sessions=sessions,
        )
        return timer

    def advance_pomodoro(self, timer_id: str) -> Timer:
        """Finish the current phase and start the next one, if any."""

        timer = self.get_timer(timer_id)
        state = timer.pomodoro

        if state is None:
            raise InvalidTimerStateError("This is not a Pomodoro timer.")
        if timer.status != TimerStatus.RUNNING:
            raise InvalidTimerStateError("Only running Pomodoros can advance.")

        if state.phase == PomodoroPhase.FOCUS:
            state.completed_sessions += 1
            if state.completed_sessions >= state.total_sessions:
                state.phase = PomodoroPhase.LONG_BREAK
                duration = state.long_break_seconds
            else:
                state.phase = PomodoroPhase.SHORT_BREAK
                duration = state.short_break_seconds
        elif state.phase == PomodoroPhase.SHORT_BREAK:
            state.phase = PomodoroPhase.FOCUS
            duration = state.focus_seconds
        else:
            return self.complete_timer(timer_id)

        timer.duration_seconds = duration
        timer.remaining_seconds = duration
        timer.end_time = datetime.now(timezone.utc) + timedelta(seconds=duration)
        return timer

    def get_timer(self, timer_id: str) -> Timer:
        """Return a timer by ID."""

        timer = self._timers.get(timer_id)

        if timer is None:
            raise TimerNotFoundError(f"Timer {timer_id!r} was not found.")

        return timer

    def get_all_timers(self) -> list[Timer]:
        """Return every timer currently held by the manager."""

        return list(self._timers.values())

    def get_user_timers(self, user_id: int) -> list[Timer]:
        """Return timers created by a specific user."""

        return [
            timer
            for timer in self._timers.values()
            if timer.creator_id == user_id
        ]

    def set_message_id(self, timer_id: str, message_id: int) -> Timer:
        """Associate a Discord message with a timer."""

        timer = self.get_timer(timer_id)
        timer.message_id = message_id
        return timer

    def pause_timer(self, timer_id: str, user_id: int) -> Timer:
        """Pause a running timer."""

        timer = self.get_timer(timer_id)
        self._validate_owner(timer, user_id)

        if timer.status != TimerStatus.RUNNING:
            raise InvalidTimerStateError("Only running timers can be paused.")

        timer.remaining_seconds = timer.get_remaining_seconds()
        timer.end_time = None
        timer.status = TimerStatus.PAUSED

        return timer

    def resume_timer(self, timer_id: str, user_id: int) -> Timer:
        """Resume a paused timer."""

        timer = self.get_timer(timer_id)
        self._validate_owner(timer, user_id)

        if timer.status != TimerStatus.PAUSED:
            raise InvalidTimerStateError("Only paused timers can be resumed.")

        remaining = timer.remaining_seconds or 0

        if remaining <= 0:
            raise InvalidTimerStateError("This timer has no remaining time.")

        timer.end_time = datetime.now(timezone.utc) + timedelta(
            seconds=remaining
        )
        timer.status = TimerStatus.RUNNING

        return timer

    def add_time(
        self,
        timer_id: str,
        user_id: int,
        seconds: int,
    ) -> Timer:
        """Add time to a running or paused timer."""

        if seconds <= 0:
            raise ValueError("Added time must be greater than zero.")

        timer = self.get_timer(timer_id)
        self._validate_owner(timer, user_id)

        if timer.status not in {
            TimerStatus.RUNNING,
            TimerStatus.PAUSED,
        }:
            raise InvalidTimerStateError(
                "Time cannot be added to a completed or cancelled timer."
            )

        timer.duration_seconds += seconds

        if timer.status == TimerStatus.RUNNING:
            current_remaining = timer.get_remaining_seconds()
            timer.remaining_seconds = current_remaining + seconds
            timer.end_time = datetime.now(timezone.utc) + timedelta(
                seconds=timer.remaining_seconds
            )
        else:
            timer.remaining_seconds = (
                timer.remaining_seconds or 0
            ) + seconds

        return timer

    def cancel_timer(self, timer_id: str, user_id: int) -> Timer:
        """Cancel an active timer."""

        timer = self.get_timer(timer_id)
        self._validate_owner(timer, user_id)

        if timer.status in {
            TimerStatus.COMPLETED,
            TimerStatus.CANCELLED,
        }:
            raise InvalidTimerStateError(
                "This timer has already finished."
            )

        timer.remaining_seconds = timer.get_remaining_seconds()
        timer.end_time = None
        timer.status = TimerStatus.CANCELLED

        return timer

    def complete_timer(self, timer_id: str) -> Timer:
        """Mark a timer as completed."""

        timer = self.get_timer(timer_id)

        if timer.status != TimerStatus.RUNNING:
            raise InvalidTimerStateError(
                "Only running timers can be completed."
            )

        timer.remaining_seconds = 0
        timer.end_time = None
        timer.status = TimerStatus.COMPLETED

        return timer

    def get_due_timers(self) -> list[Timer]:
        """Return running timers whose completion time has passed."""

        return [
            timer
            for timer in self._timers.values()
            if timer.is_finished()
        ]

    def remove_timer(self, timer_id: str) -> None:
        """Remove a timer from the manager."""

        self.get_timer(timer_id)
        del self._timers[timer_id]

    @staticmethod
    def _validate_owner(timer: Timer, user_id: int) -> None:
        """Ensure that a user owns the timer."""

        if timer.creator_id != user_id:
            raise TimerPermissionError(
                "Only the timer creator can control this timer."
            )
