from __future__ import annotations

import math
import random

import pygame
from pygame.math import Vector2

from animation import Tween
from rendering import (
    draw_curved_connection,
    draw_glow_circle,
    draw_node_shadow,
    draw_pixel_disc,
    draw_pixel_panel,
    draw_pixel_ring,
    draw_text_centralizado,
)
from scene_base import SceneBase
from settings import (
    BLUE_ACC,
    DARK,
    GLOW_COLOR,
    NODE_COMPLETED,
    NODE_LOCKED,
    NODE_RADIUS,
    NODE_UNLOCKED,
    OVERWORLD_ENTRY_FADE_SPEED,
    PANEL_BORDER,
    PANEL_COLOR,
    PINK_ACC,
    PLAYER_MOVE_COOLDOWN,
    PLAYER_MOVE_DURATION,
    PRIMARY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SELECTION_COLOR,
    TEXT_COLOR,
    WHITE,
    YELLOW_ACC,
    blend_color,
    with_alpha,
)


class OverworldScene(SceneBase):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.move_cooldown = PLAYER_MOVE_COOLDOWN
        self.move_timer = 0.0
        self.scene_time = 0.0

        self.hovered_node_id: int | None = None
        self.travel_target_node_id: int | None = None
        self.travel_tween: Tween | None = None

        start_position = Vector2(self.game.nodes[self.game.current_node_id]["pos"])
        self.player_position = start_position
        self.entry_fade_alpha = 190.0
        self.entry_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        self.selector_sprite = self.game.selector_sprite
        self.selector_shadow = pygame.Surface((74, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(
            self.selector_shadow,
            with_alpha(DARK, 90),
            pygame.Rect(0, 0, 74, 20),
        )

        self.map_surface = self._build_map_background()

        self.celebration_active = False
        self.celebration_timer = 0.0
        self.celebration_particles: list[dict[str, object]] = []

    def on_enter(self, previous_scene) -> None:
        _ = previous_scene
        self.entry_fade_alpha = 160.0
        self.travel_tween = None
        self.travel_target_node_id = None
        self.player_position = Vector2(self.game.nodes[self.game.current_node_id]["pos"])
        if self.game.pending_congrats_animation:
            self.game.pending_congrats_animation = False
            self._start_congrats_animation()

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self.celebration_active:
            # Qualquer tecla encerra a celebracao apos exibir.
            self.celebration_active = False
            self.celebration_particles.clear()
            return

        if event.key == pygame.K_RETURN:
            if not self._is_player_moving():
                self._open_quiz_for_current_node()
            return

        if self.move_timer > 0.0 or self._is_player_moving():
            return

        direction = self._direction_from_key(event.key)
        if direction is None:
            return

        target_node_id = self._choose_neighbor(direction)
        if target_node_id is None:
            return

        self._start_player_travel(target_node_id)
        self.move_timer = self.move_cooldown

    def update(self, dt: float) -> None:
        self.scene_time += dt
        self.move_timer = max(0.0, self.move_timer - dt)
        self._update_hover_node()
        self._update_player_travel(dt)
        self._update_celebration(dt)

        if self.entry_fade_alpha > 0.0:
            self.entry_fade_alpha = max(
                0.0, self.entry_fade_alpha - OVERWORLD_ENTRY_FADE_SPEED * dt
            )

    def draw(self, screen) -> None:
        screen.blit(self.map_surface, (0, 0))
        self._draw_connections(screen)
        self._draw_nodes(screen)
        self._draw_selector(screen)
        self._draw_bottom_panel(screen)
        self._draw_congrats_overlay(screen)
        self._draw_entry_fade(screen)

    def _build_map_background(self) -> pygame.Surface:
        surface = self.game.background_gradient.copy()

        map_rect = pygame.Rect(46, 54, SCREEN_WIDTH - 92, SCREEN_HEIGHT - 188)
        draw_pixel_panel(
            surface,
            map_rect,
            with_alpha(blend_color(WHITE, YELLOW_ACC, 0.26), 244),
            with_alpha(blend_color(PRIMARY, WHITE, 0.42), 255),
            border_size=6,
            shadow_color=with_alpha(DARK, 86),
            shadow_offset=(8, 8),
        )

        for y in range(map_rect.y + 6, map_rect.bottom - 6):
            t = (y - map_rect.y) / max(1, map_rect.height)
            grad = blend_color(
                blend_color(WHITE, YELLOW_ACC, 0.40),
                blend_color(YELLOW_ACC, PRIMARY, 0.36),
                t,
            )
            pygame.draw.line(
                surface,
                with_alpha(grad, 86),
                (map_rect.x + 6, y),
                (map_rect.right - 6, y),
                1,
            )

        land_light = blend_color(YELLOW_ACC, WHITE, 0.42)
        land_dark = blend_color(land_light, PRIMARY, 0.22)
        region_specs = [
            ((180, 340), 150, land_dark),
            ((340, 260), 140, land_light),
            ((470, 410), 168, land_dark),
            ((640, 270), 132, land_light),
            ((790, 405), 146, land_dark),
        ]
        for center, radius, color in region_specs:
            draw_pixel_disc(
                surface,
                center,
                radius + 24,
                with_alpha(blend_color(color, WHITE, 0.46), 64),
                pixel_size=8,
            )
            draw_pixel_disc(
                surface,
                center,
                radius,
                with_alpha(color, 220),
                pixel_size=6,
            )
            draw_pixel_ring(
                surface,
                center,
                radius + 8,
                with_alpha(blend_color(color, PRIMARY, 0.26), 190),
                thickness=5,
                pixel_size=5,
            )

        grid_color = with_alpha(blend_color(PRIMARY, WHITE, 0.56), 50)
        for x in range(map_rect.x + 32, map_rect.right - 32, 88):
            pygame.draw.line(
                surface,
                grid_color,
                (x, map_rect.y + 20),
                (x, map_rect.bottom - 20),
                1,
            )
        for y in range(map_rect.y + 28, map_rect.bottom - 24, 70):
            pygame.draw.line(
                surface,
                grid_color,
                (map_rect.x + 20, y),
                (map_rect.right - 20, y),
                1,
            )

        rng = random.Random(2026)
        foliage_light = with_alpha(blend_color(YELLOW_ACC, WHITE, 0.46), 145)
        foliage_dark = with_alpha(blend_color(land_dark, PRIMARY, 0.38), 150)
        for _ in range(170):
            px = rng.randint(map_rect.x + 22, map_rect.right - 22)
            py = rng.randint(map_rect.y + 18, map_rect.bottom - 18)
            if (px + py) % 5 == 0:
                color = foliage_dark
            else:
                color = foliage_light
            pygame.draw.rect(surface, color, pygame.Rect(px, py, 3, 3))

        return surface

    def _draw_connections(self, screen) -> None:
        road_shadow = blend_color(DARK, PRIMARY, 0.25)
        road_color = blend_color(YELLOW_ACC, PRIMARY, 0.50)
        for start_id, end_id in self.game.edges:
            start_pos = self.game.nodes[start_id]["pos"]
            end_pos = self.game.nodes[end_id]["pos"]
            draw_curved_connection(
                screen,
                (start_pos[0], start_pos[1] + 2),
                (end_pos[0], end_pos[1] + 2),
                road_shadow,
                width=10,
            )
            draw_curved_connection(screen, start_pos, end_pos, road_color, width=6)

    def _draw_nodes(self, screen) -> None:
        for node_id in self.game.node_ids:
            position = self.game.nodes[node_id]["pos"]
            is_current = node_id == self.game.current_node_id and not self._is_player_moving()
            is_hovered = node_id == self.hovered_node_id
            is_unlocked = node_id in self.game.unlocked_nodes
            is_completed = node_id in self.game.completed_nodes

            node_radius = float(NODE_RADIUS + 4)
            if is_current:
                node_radius *= 1.0 + 0.10 * math.sin(self.scene_time * 4.0)
            if is_hovered:
                node_radius += 3.0
            node_radius_int = int(node_radius)

            draw_node_shadow(screen, position, node_radius_int, DARK)
            if is_unlocked:
                draw_glow_circle(
                    screen,
                    position,
                    radius=node_radius_int + 18,
                    color=GLOW_COLOR,
                    base_alpha=95 if is_current else 65,
                    steps=4,
                )

            node_color = self._get_node_color(node_id)
            draw_pixel_disc(screen, position, node_radius_int, node_color, pixel_size=4)
            draw_pixel_disc(
                screen,
                (position[0] - node_radius_int // 3, position[1] - node_radius_int // 3),
                max(4, node_radius_int // 3),
                with_alpha(WHITE, 110),
                pixel_size=4,
            )
            draw_pixel_ring(screen, position, node_radius_int + 2, PRIMARY, thickness=5, pixel_size=4)

            if is_hovered:
                draw_pixel_ring(
                    screen,
                    position,
                    node_radius_int + 8,
                    SELECTION_COLOR,
                    thickness=4,
                    pixel_size=4,
                )

            if is_completed:
                draw_pixel_disc(screen, position, 8, with_alpha(WHITE, 200), pixel_size=2)

    def _draw_selector(self, screen) -> None:
        base_y = self.player_position.y - 6
        bob = 3.0 * math.sin(self.scene_time * 5.2)
        if self._is_player_moving():
            bob = 0.0

        center_x = int(self.player_position.x)
        center_y = int(base_y + bob)

        shadow_rect = self.selector_shadow.get_rect(center=(center_x, center_y + 22))
        sprite_rect = self.selector_sprite.get_rect(midbottom=(center_x, center_y + 18))

        screen.blit(self.selector_shadow, shadow_rect)
        screen.blit(self.selector_sprite, sprite_rect)

    def _draw_bottom_panel(self, screen) -> None:
        panel_rect = pygame.Rect(34, SCREEN_HEIGHT - 106, SCREEN_WIDTH - 68, 76)
        draw_pixel_panel(
            screen,
            panel_rect,
            with_alpha(PANEL_COLOR, 222),
            with_alpha(PANEL_BORDER, 250),
            border_size=4,
            shadow_color=with_alpha(DARK, 90),
            shadow_offset=(6, 6),
        )

        progress_text = f"QUIZZES: {len(self.game.completed_nodes)}/{len(self.game.node_ids)}"
        controls_text = "SETAS MOVER | ENTER QUIZ | ESC MENU"

        screen.blit(
            self.game.font_ui.render(progress_text, False, TEXT_COLOR),
            (52, SCREEN_HEIGHT - 96),
        )
        screen.blit(
            self.game.font_ui.render(controls_text, False, TEXT_COLOR),
            (430, SCREEN_HEIGHT - 96),
        )

    def _draw_entry_fade(self, screen) -> None:
        if self.entry_fade_alpha <= 0.0:
            return
        self.entry_overlay.fill(with_alpha(DARK, int(self.entry_fade_alpha)))
        screen.blit(self.entry_overlay, (0, 0))

    def _start_congrats_animation(self) -> None:
        self.celebration_active = True
        self.celebration_timer = 0.0
        self.celebration_particles.clear()
        for _ in range(120):
            self.celebration_particles.append(self._new_particle())

    def _new_particle(self) -> dict[str, object]:
        return {
            "pos": Vector2(
                random.randint(80, SCREEN_WIDTH - 80),
                random.randint(-80, SCREEN_HEIGHT // 2),
            ),
            "vel": Vector2(random.uniform(-50.0, 50.0), random.uniform(35.0, 120.0)),
            "life": random.uniform(1.4, 3.8),
            "size": random.choice((4, 6, 8)),
            "color": random.choice((YELLOW_ACC, PINK_ACC, BLUE_ACC, WHITE)),
        }

    def _update_celebration(self, dt: float) -> None:
        if not self.celebration_active:
            return

        self.celebration_timer += dt
        for particle in self.celebration_particles:
            particle["life"] = float(particle["life"]) - dt
            particle["pos"] += particle["vel"] * dt
            particle["vel"] += Vector2(0.0, 75.0) * dt

        self.celebration_particles = [
            particle
            for particle in self.celebration_particles
            if float(particle["life"]) > 0.0 and float(particle["pos"].y) < SCREEN_HEIGHT + 20
        ]

        while len(self.celebration_particles) < 120:
            self.celebration_particles.append(self._new_particle())

        if self.celebration_timer >= 6.0:
            self.celebration_active = False
            self.celebration_particles.clear()

    def _draw_congrats_overlay(self, screen) -> None:
        if not self.celebration_active:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(with_alpha(DARK, 120))
        screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(120, 180, SCREEN_WIDTH - 240, 300)
        draw_pixel_panel(
            screen,
            panel_rect,
            with_alpha(PANEL_COLOR, 236),
            with_alpha(SELECTION_COLOR, 255),
            border_size=6,
            shadow_color=with_alpha(DARK, 130),
            shadow_offset=(10, 10),
        )

        for particle in self.celebration_particles:
            pos = particle["pos"]
            size = int(particle["size"])
            color = particle["color"]
            pygame.draw.rect(screen, color, pygame.Rect(int(pos.x), int(pos.y), size, size))

        pulse = 1.0 + 0.04 * math.sin(self.scene_time * 8.0)
        draw_text_centralizado(
            screen,
            self.game.font_title,
            "PARABENS!",
            PRIMARY,
            (panel_rect.centerx, int(panel_rect.y + 90 * pulse)),
        )
        draw_text_centralizado(
            screen,
            self.game.font_small,
            "VOCE CONCLUIU TODOS OS QUIZZES",
            TEXT_COLOR,
            (panel_rect.centerx, panel_rect.y + 178),
        )
        draw_text_centralizado(
            screen,
            self.game.font_ui,
            "APERTE QUALQUER TECLA",
            TEXT_COLOR,
            (panel_rect.centerx, panel_rect.y + 238),
        )

    def _update_hover_node(self) -> None:
        mouse_position = Vector2(pygame.mouse.get_pos())
        nearest_id = None
        nearest_distance = float("inf")

        for node_id in self.game.node_ids:
            node_pos = Vector2(self.game.nodes[node_id]["pos"])
            distance = mouse_position.distance_to(node_pos)
            if distance <= NODE_RADIUS + 14 and distance < nearest_distance:
                nearest_distance = distance
                nearest_id = node_id

        self.hovered_node_id = nearest_id

    def _update_player_travel(self, dt: float) -> None:
        if self.travel_tween is None:
            current_pos = Vector2(self.game.nodes[self.game.current_node_id]["pos"])
            self.player_position = current_pos
            return

        self.player_position = self.travel_tween.update(dt)
        if not self.travel_tween.finished:
            return

        if self.travel_target_node_id is not None:
            self.game.current_node_id = self.travel_target_node_id
        self.player_position = Vector2(self.game.nodes[self.game.current_node_id]["pos"])
        self.travel_target_node_id = None
        self.travel_tween = None

    def _open_quiz_for_current_node(self) -> None:
        node_id = self.game.current_node_id
        if node_id not in self.game.unlocked_nodes:
            return

        from scenes.quiz import QuizScene

        self.game.transition_to(QuizScene(self.game, self.game.nodes[node_id]))

    def _start_player_travel(self, target_node_id: int) -> None:
        current_position = Vector2(self.game.nodes[self.game.current_node_id]["pos"])
        target_position = Vector2(self.game.nodes[target_node_id]["pos"])
        self.travel_tween = Tween(current_position, target_position, PLAYER_MOVE_DURATION)
        self.travel_target_node_id = target_node_id

    def _choose_neighbor(self, direction: Vector2) -> int | None:
        current_id = self.game.current_node_id
        current_pos = Vector2(self.game.nodes[current_id]["pos"])

        best_neighbor = None
        best_score = 0.34
        best_distance = float("inf")

        for neighbor_id in self.game.neighbors.get(current_id, []):
            if neighbor_id not in self.game.unlocked_nodes:
                continue

            neighbor_pos = Vector2(self.game.nodes[neighbor_id]["pos"])
            move_vector = neighbor_pos - current_pos
            if move_vector.length_squared() == 0.0:
                continue

            direction_score = move_vector.normalize().dot(direction)
            distance = move_vector.length_squared()
            if direction_score > best_score or (
                direction_score == best_score and distance < best_distance
            ):
                best_neighbor = neighbor_id
                best_score = direction_score
                best_distance = distance

        return best_neighbor

    def _direction_from_key(self, key) -> Vector2 | None:
        if key == pygame.K_LEFT:
            return Vector2(-1, 0)
        if key == pygame.K_RIGHT:
            return Vector2(1, 0)
        if key == pygame.K_UP:
            return Vector2(0, -1)
        if key == pygame.K_DOWN:
            return Vector2(0, 1)
        return None

    def _is_player_moving(self) -> bool:
        return self.travel_tween is not None

    def _get_node_color(self, node_id: int):
        if node_id in self.game.completed_nodes:
            return NODE_COMPLETED
        if node_id in self.game.unlocked_nodes:
            return NODE_UNLOCKED
        return NODE_LOCKED
