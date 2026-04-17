from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SOPStep:
    """One SOP step rendered in the HUD."""

    name: str


@dataclass(frozen=True)
class HUDState:
    """Current HUD state for rendering on a second screen."""

    current_step: str | None
    completed_steps: int
    total_steps: int
    overlay_color: str = "black"


class SOPTracker:
    """Tracks SOP progress from visual detections."""

    def __init__(self, steps: Sequence[SOPStep] | Iterable[SOPStep]):
        self._steps = list(steps)
        self._completed = 0

    @property
    def completed_steps(self) -> int:
        return self._completed

    @property
    def total_steps(self) -> int:
        return len(self._steps)

    @property
    def current_step(self) -> str | None:
        if self._completed >= self.total_steps:
            return None
        return self._steps[self._completed].name

    def mark_detected(self, step_detected: bool) -> None:
        if step_detected and self._completed < self.total_steps:
            self._completed += 1


class HUDController:
    """Minimal HUD controller implementation entry-point."""

    def __init__(self, steps: Sequence[SOPStep] | Iterable[SOPStep], overlay_color: str = "black"):
        self._tracker = SOPTracker(steps)
        self._overlay_color = overlay_color

    def process_frame(self, frame: object, step_detected: bool) -> HUDState:
        """Process a camera frame and update SOP progress.

        `frame` is accepted as an opaque object so callers can wire any camera backend.
        """
        _ = frame
        self._tracker.mark_detected(step_detected=step_detected)
        return HUDState(
            current_step=self._tracker.current_step,
            completed_steps=self._tracker.completed_steps,
            total_steps=self._tracker.total_steps,
            overlay_color=self._overlay_color,
        )
