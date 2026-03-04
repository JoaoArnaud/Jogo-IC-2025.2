from __future__ import annotations

import math
import random

import pygame

from scene_base import SceneBase
from settings import (
    BLUE_ACC,
    DARK,
    PINK_ACC,
    PRIMARY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    blend_color,
    with_alpha,
)


class StartScene(SceneBase):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.background, self.scanline_overlay = self._build_background_layers()
        self.rng = random.Random(2026)
        self.stars = self._build_stars(260)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            self.game.enter_game_state()

    def update(self, dt: float) -> None:
        self._update_stars(dt)

    def draw(self, screen) -> None:
        screen.blit(self.background, (0, 0))
        self._draw_stars(screen)
        screen.blit(self.scanline_overlay, (0, 0))
        self._draw_title(screen)
        self._draw_prompt(screen)

    def _build_background_layers(self) -> tuple[pygame.Surface, pygame.Surface]:
        background = self.game.background_gradient.copy()

        # Escurece o gradiente base para um clima retro simples.
        dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dark_overlay.fill(with_alpha(DARK, 92))
        background.blit(dark_overlay, (0, 0))

        # Scanlines leves para textura de monitor antigo.
        scanline_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        scanline_color = with_alpha(blend_color(PRIMARY, DARK, 0.40), 48)
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(scanline_overlay, scanline_color, (0, y), (SCREEN_WIDTH, y), 1)

        return background, scanline_overlay

    def _build_stars(self, count: int) -> list[dict[str, float | int | tuple[int, int, int]]]:
        stars: list[dict[str, float | int | tuple[int, int, int]]] = []
        for _ in range(count):
            stars.append(self._create_star(initial_spawn=True))
        return stars

    def _create_star(self, initial_spawn: bool) -> dict[str, float | int | tuple[int, int, int]]:
        star_palette = (
            WHITE,
            BLUE_ACC,
            PINK_ACC,
            blend_color(WHITE, PRIMARY, 0.36),
        )
        size = self.rng.choice((1, 2, 2, 3))
        speed = self.rng.uniform(10.0, 24.0) + size * 3.6
        alpha = self.rng.randint(75, 205)
        x = self.rng.uniform(0, SCREEN_WIDTH - size)
        if initial_spawn:
            y = self.rng.uniform(0, SCREEN_HEIGHT - size)
        else:
            y = -float(size) - self.rng.uniform(4.0, 90.0)
        return {
            "x": x,
            "y": y,
            "size": size,
            "speed": speed,
            "alpha": alpha,
            "color": self.rng.choice(star_palette),
            "phase": self.rng.uniform(0.0, 6.28318),
        }

    def _update_stars(self, dt: float) -> None:
        for idx, star in enumerate(self.stars):
            star["y"] = float(star["y"]) + float(star["speed"]) * dt
            if float(star["y"]) > SCREEN_HEIGHT + int(star["size"]):
                self.stars[idx] = self._create_star(initial_spawn=False)

    def _draw_stars(self, screen) -> None:
        time_seconds = pygame.time.get_ticks() / 1000.0
        for star in self.stars:
            twinkle = 0.70 + 0.30 * math.sin(time_seconds * 3.0 + float(star["phase"]))
            alpha = int(max(40, min(230, int(star["alpha"]) * twinkle)))
            color = with_alpha(star["color"], alpha)
            size = int(star["size"])
            rect = pygame.Rect(int(star["x"]), int(star["y"]), size, size)
            pygame.draw.rect(screen, color, rect)

    def _draw_title(self, screen) -> None:
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 72)
        self._draw_outlined_text(
            screen,
            self.game.font_title,
            "NEURAL QUEST",
            blend_color(WHITE, BLUE_ACC, 0.22),
            blend_color(PRIMARY, DARK, 0.58),
            center,
        )

    def _draw_prompt(self, screen) -> None:
        is_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if not is_visible:
            return

        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 26)
        self._draw_outlined_text(
            screen,
            self.game.font_medium,
            "PRESS ANY KEY TO START",
            blend_color(WHITE, BLUE_ACC, 0.34),
            blend_color(PRIMARY, DARK, 0.52),
            center,
        )

    def _draw_outlined_text(
        self,
        screen,
        font,
        text: str,
        text_color,
        outline_color,
        center: tuple[int, int],
    ) -> None:
        for offset_x, offset_y in (
            (-4, 0),
            (4, 0),
            (0, -4),
            (0, 4),
            (-4, -4),
            (4, -4),
            (-4, 4),
            (4, 4),
        ):
            shadow = font.render(text, False, outline_color)
            shadow_rect = shadow.get_rect(center=(center[0] + offset_x, center[1] + offset_y))
            screen.blit(shadow, shadow_rect)

        text_surface = font.render(text, False, text_color)
        text_rect = text_surface.get_rect(center=center)
        screen.blit(text_surface, text_rect)
