from __future__ import annotations

import math
from typing import Callable

from pygame.math import Vector2


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def lerp(a, b, t: float):
    """Interpolacao para float e Vector2."""
    clamped = clamp01(t)
    return a + (b - a) * clamped


def ease_in_out_sine(t: float) -> float:
    clamped = clamp01(t)
    return -(math.cos(math.pi * clamped) - 1.0) / 2.0


class Tween:
    """Tween simples para animacoes com delta time."""

    def __init__(
        self,
        start: float | Vector2,
        end: float | Vector2,
        duration: float,
        ease: Callable[[float], float] | None = None,
    ) -> None:
        self.start = start
        self.end = end
        self.duration = max(0.0001, duration)
        self.ease = ease or ease_in_out_sine
        self.elapsed = 0.0
        self.finished = False
        self.value = start

    def update(self, dt: float):
        if self.finished:
            return self.value

        self.elapsed = min(self.duration, self.elapsed + dt)
        linear_t = self.elapsed / self.duration
        eased_t = self.ease(linear_t)
        self.value = lerp(self.start, self.end, eased_t)

        if self.elapsed >= self.duration:
            self.finished = True
            self.value = self.end

        return self.value

    def reset(self) -> None:
        self.elapsed = 0.0
        self.finished = False
        self.value = self.start
