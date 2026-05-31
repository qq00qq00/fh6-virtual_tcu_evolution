"""Abstract interface for shift output — keyboard, gamepad, or future backends.

All concrete implementations must provide the full surface below so
TCULogic (and ReverseHoldDetector) can treat them interchangeably.
"""

from abc import ABC, abstractmethod


class OutputInterface(ABC):
    """Contract for injecting shift commands into the game."""

    @property
    @abstractmethod
    def key_up(self) -> str:
        """Human-readable label for the upshift action (e.g. 'E' or 'A')."""
        ...

    @property
    @abstractmethod
    def key_down(self) -> str:
        """Human-readable label for the downshift action (e.g. 'Q' or 'X')."""
        ...

    @abstractmethod
    def is_self_press(self, key: str) -> bool:
        """Return True if *key* was injected by this output within the
        self-press window.  Used by paddle listeners to ignore echo when
        the TCU fires a shift and the game also reports a paddle press.

        Gamepad outputs that don't have an echo problem may return False
        unconditionally."""
        ...

    @abstractmethod
    def shift_to(self, from_gear: int, target_gear: int):
        """Trigger a shift to the specified gear (non-blocking)."""
        ...

    def set_brake(self, brake: float) -> None:  # noqa: B027
        """Report the current physical brake position (0.0-1.0).

        Outputs that emit a full device-state packet on every action (the
        virtual gamepad) can mirror this onto their brake axis so injecting a
        shift does not momentarily zero the player's real brake input.
        Default: no-op — keyboard and vjoy do not share an XInput state
        packet with the physical controller."""

    @abstractmethod
    def shutdown(self):
        """Release any OS resources (thread pools, device handles, hooks)."""
        ...
