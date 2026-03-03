from __future__ import annotations

from pathlib import Path

import pygame

from levels import EDGES, NEIGHBORS, NODES
from rendering import (
    PixelFont,
    build_vertical_gradient,
    create_player_sprite,
    draw_pixel_panel,
    draw_text_centralizado,
)
from scenes.overworld import OverworldScene
from settings import (
    BACKGROUND_BOTTOM,
    BACKGROUND_TOP,
    DARK,
    FPS,
    PANEL_BORDER,
    PANEL_COLOR,
    PINK_ACC,
    PRIMARY,
    SCENE_FADE_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WINDOW_TITLE,
    WHITE,
    with_alpha,
)


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.FULLSCREEN | pygame.SCALED,
        )
        self.clock = pygame.time.Clock()
        self.running = True

        # Dados do mapa
        self.nodes = {node["id"]: node for node in NODES}
        self.node_ids = [node["id"] for node in NODES]
        self.edges = EDGES
        self.neighbors = NEIGHBORS

        # Progresso do jogador
        self.unlocked_nodes = {0}
        self.completed_nodes: set[int] = set()
        self.current_node_id = 0
        self.all_quiz_completed = False
        self.pending_congrats_animation = False

        # Recursos compartilhados
        self.background_gradient = build_vertical_gradient(
            (SCREEN_WIDTH, SCREEN_HEIGHT), BACKGROUND_TOP, BACKGROUND_BOTTOM
        )
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Fontes carregadas uma unica vez
        self.font_small = PixelFont(34, scale=3, family="Courier New", bold=True)
        self.font_medium = PixelFont(48, scale=3, family="Courier New", bold=True)
        self.font_large = PixelFont(64, scale=3, family="Courier New", bold=True)
        self.font_title = PixelFont(80, scale=3, family="Courier New", bold=True)
        self.font_ui = PixelFont(24, scale=2, family="Courier New", bold=True)

        # Sprite do aluno para selecao no mapa
        self.selector_sprite = self._load_selector_sprite()

        # Estado de cena
        self.overworld_scene = OverworldScene(self)
        self.current_scene = self.overworld_scene
        self.current_scene.on_enter(None)

        # Transicao global entre cenas
        self.transition_state = "none"  # none | fade_out | fade_in
        self.transition_alpha = 0.0
        self.next_scene = None

        # Menu global de pausa/saida
        self.pause_menu_active = False
        self.pause_menu_index = 0
        self.pause_menu_options = ("CONTINUAR", "SAIR DO JOGO")

    def change_scene(self, new_scene) -> None:
        """Mudanca instantanea (fallback); prefira transition_to."""
        self.pause_menu_active = False
        previous = self.current_scene
        previous.on_exit(new_scene)
        self.current_scene = new_scene
        self.current_scene.on_enter(previous)

    def transition_to(self, new_scene) -> None:
        if self.transition_state != "none":
            return
        self.pause_menu_active = False
        self.next_scene = new_scene
        self.transition_state = "fade_out"
        self.transition_alpha = 0.0

    def _load_selector_sprite(self) -> pygame.Surface:
        asset_path = Path(__file__).resolve().parent / "assets" / "aluno_cdia.png"
        try:
            raw_sprite = pygame.image.load(str(asset_path)).convert_alpha()
            return pygame.transform.scale(
                raw_sprite,
                (raw_sprite.get_width() * 2, raw_sprite.get_height() * 2),
            )
        except (pygame.error, FileNotFoundError):
            return create_player_sprite(PRIMARY, PINK_ACC, WHITE, DARK)

    def _handle_global_event(self, event) -> bool:
        if event.type != pygame.KEYDOWN or self.transition_state != "none":
            return False

        if event.key == pygame.K_ESCAPE:
            self.pause_menu_active = not self.pause_menu_active
            self.pause_menu_index = 0
            return True

        if not self.pause_menu_active:
            return False

        if event.key in (pygame.K_UP, pygame.K_w):
            self.pause_menu_index = (self.pause_menu_index - 1) % len(
                self.pause_menu_options
            )
            return True

        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.pause_menu_index = (self.pause_menu_index + 1) % len(
                self.pause_menu_options
            )
            return True

        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            selected = self.pause_menu_options[self.pause_menu_index]
            if selected == "CONTINUAR":
                self.pause_menu_active = False
            else:
                self.running = False
            return True

        return True

    def _draw_pause_menu(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(with_alpha(DARK, 150))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 330,
            SCREEN_HEIGHT // 2 - 165,
            660,
            330,
        )
        draw_pixel_panel(
            self.screen,
            panel_rect,
            with_alpha(PANEL_COLOR, 242),
            with_alpha(PANEL_BORDER, 255),
            border_size=5,
            shadow_color=with_alpha(DARK, 110),
            shadow_offset=(8, 8),
        )

        draw_text_centralizado(
            self.screen,
            self.font_medium,
            "MENU",
            PRIMARY,
            (panel_rect.centerx, panel_rect.y + 56),
        )

        for idx, option in enumerate(self.pause_menu_options):
            option_rect = pygame.Rect(
                panel_rect.x + 58,
                panel_rect.y + 110 + idx * 96,
                panel_rect.width - 116,
                74,
            )
            is_selected = idx == self.pause_menu_index
            fill = with_alpha(PANEL_COLOR, 255) if is_selected else with_alpha(WHITE, 220)
            border = with_alpha(PRIMARY, 255) if is_selected else with_alpha(PANEL_BORDER, 255)
            draw_pixel_panel(self.screen, option_rect, fill, border, border_size=4)

            text_color = PRIMARY if is_selected else TEXT_COLOR
            draw_text_centralizado(
                self.screen,
                self.font_small,
                option,
                text_color,
                option_rect.center,
            )

        hint = self.font_ui.render("ESC FECHA MENU", False, TEXT_COLOR)
        hint_rect = hint.get_rect(center=(panel_rect.centerx, panel_rect.bottom - 20))
        self.screen.blit(hint, hint_rect)

    def handle_quiz_result(self, node_id: int, is_correct: bool) -> None:
        if not is_correct:
            return

        self.completed_nodes.add(node_id)
        for neighbor_id in self.neighbors.get(node_id, []):
            self.unlocked_nodes.add(neighbor_id)

        if (
            not self.all_quiz_completed
            and len(self.completed_nodes) == len(self.node_ids)
        ):
            self.all_quiz_completed = True
            self.pending_congrats_animation = True

    def _update_transition(self, dt: float) -> None:
        if self.transition_state == "none":
            return

        self.transition_alpha += SCENE_FADE_SPEED * dt * (
            1.0 if self.transition_state == "fade_out" else -1.0
        )

        if self.transition_state == "fade_out" and self.transition_alpha >= 255.0:
            self.transition_alpha = 255.0
            previous_scene = self.current_scene
            if self.next_scene is not None:
                previous_scene.on_exit(self.next_scene)
                self.current_scene = self.next_scene
                self.current_scene.on_enter(previous_scene)
            self.next_scene = None
            self.transition_state = "fade_in"

        if self.transition_state == "fade_in" and self.transition_alpha <= 0.0:
            self.transition_alpha = 0.0
            self.transition_state = "none"

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                if self._handle_global_event(event):
                    continue
                if self.transition_state == "none" and not self.pause_menu_active:
                    self.current_scene.handle_event(event)

            if not self.pause_menu_active:
                self.current_scene.update(dt)
            self._update_transition(dt)
            self.current_scene.draw(self.screen)

            if self.transition_state != "none":
                alpha = int(max(0.0, min(255.0, self.transition_alpha)))
                self.fade_surface.fill(with_alpha(DARK, alpha))
                self.screen.blit(self.fade_surface, (0, 0))

            if self.pause_menu_active:
                self._draw_pause_menu()

            pygame.display.flip()

        pygame.quit()
