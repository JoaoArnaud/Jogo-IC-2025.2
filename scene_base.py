from __future__ import annotations


class SceneBase:
    """Interface base para todas as cenas do jogo."""

    def __init__(self, game):
        self.game = game

    def on_enter(self, previous_scene) -> None:
        _ = previous_scene

    def on_exit(self, next_scene) -> None:
        _ = next_scene

    def handle_event(self, event) -> None:
        raise NotImplementedError

    def update(self, dt: float) -> None:
        raise NotImplementedError

    def draw(self, screen) -> None:
        raise NotImplementedError
