from __future__ import annotations

import math

import pygame

from rendering import (
    draw_pixel_panel,
    draw_text_centralizado,
    truncate_with_ellipsis,
    wrap_text,
)
from scene_base import SceneBase
from settings import (
    BLUE_ACC,
    DARK,
    ERROR_COLOR,
    PRIMARY,
    QUIZ_CARD_HEIGHT,
    QUIZ_CARD_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SELECTION_COLOR,
    SUCCESS_COLOR,
    TEXT_COLOR,
    WHITE,
    blend_color,
    with_alpha,
)


class QuizScene(SceneBase):
    def __init__(self, game, node_data) -> None:
        super().__init__(game)
        self.node_id = node_data["id"]
        self.question = node_data["quiz"]["question"]
        self.options = node_data["quiz"]["options"]
        self.correct_index = node_data["quiz"]["correct_index"]

        self.selected_index = 0
        self.answered = False
        self.is_correct = False
        self.feedback_text = ""

        self.scene_time = 0.0
        self.feedback_time = 0.0
        self.shake_time = 0.0

        card_width = min(max(QUIZ_CARD_WIDTH, 900), SCREEN_WIDTH - 32)
        card_height = min(max(QUIZ_CARD_HEIGHT, 660), SCREEN_HEIGHT - 20)
        self.card_rect = pygame.Rect(
            (SCREEN_WIDTH - card_width) // 2,
            (SCREEN_HEIGHT - card_height) // 2,
            card_width,
            card_height,
        )
        self.dim_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dim_surface.fill(with_alpha(DARK, 125))

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self.answered:
            self.game.transition_to(self.game.overworld_scene)
            return

        if event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            return

        if event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return

        if pygame.K_1 <= event.key <= pygame.K_4:
            choice = event.key - pygame.K_1
            if choice < len(self.options):
                self.selected_index = choice
            return

        if event.key == pygame.K_RETURN:
            self._submit_answer()

    def update(self, dt: float) -> None:
        self.scene_time += dt
        if self.answered:
            self.feedback_time += dt
        if self.shake_time > 0.0:
            self.shake_time = max(0.0, self.shake_time - dt)

    def draw(self, screen) -> None:
        screen.blit(self.game.background_gradient, (0, 0))
        screen.blit(self.dim_surface, (0, 0))

        shake_offset = self._current_shake_offset()
        card_rect = self.card_rect.move(shake_offset, 0)
        self._draw_card_shadow(screen, card_rect)
        self._draw_card(screen, card_rect)

    def _draw_card_shadow(self, screen, card_rect: pygame.Rect) -> None:
        draw_pixel_panel(
            screen,
            card_rect.inflate(12, 12).move(0, 6),
            with_alpha(DARK, 110),
            with_alpha(DARK, 110),
            border_size=2,
        )

    def _draw_card(self, screen, card_rect: pygame.Rect) -> None:
        draw_pixel_panel(
            screen,
            card_rect,
            with_alpha(WHITE, 244),
            with_alpha(blend_color(PRIMARY, WHITE, 0.45), 255),
            border_size=4,
        )

        content_left = card_rect.x + 32
        content_right = card_rect.right - 32
        content_width = content_right - content_left
        accent_rect = pygame.Rect(content_left, card_rect.y + 20, content_width, 8)
        pygame.draw.rect(
            screen,
            with_alpha(blend_color(SELECTION_COLOR, WHITE, 0.32), 255),
            accent_rect,
        )

        status_height = max(122, self.game.font_ui.get_height() * 3 + 30)
        status_rect = pygame.Rect(
            content_left,
            card_rect.bottom - 22 - status_height,
            content_width,
            status_height,
        )

        question_top = card_rect.y + 48
        minimum_options_area = 250
        available_for_question = max(
            82,
            min(160, status_rect.top - question_top - minimum_options_area),
        )
        question_lines, question_font = self._fit_question_lines(
            max_width=content_width - 36,
            max_height=available_for_question,
        )

        question_line_height = question_font.get_height() + 4
        question_block_height = max(
            question_font.get_height() + 20,
            len(question_lines) * question_line_height + 16,
        )
        question_rect = pygame.Rect(
            content_left,
            question_top,
            content_width,
            question_block_height,
        )
        draw_pixel_panel(
            screen,
            question_rect,
            with_alpha(blend_color(WHITE, BLUE_ACC, 0.08), 235),
            with_alpha(blend_color(PRIMARY, WHITE, 0.52), 255),
            border_size=3,
        )

        question_y = question_rect.y + 8 + question_font.get_height() // 2
        for line in question_lines:
            draw_text_centralizado(
                screen,
                question_font,
                line,
                TEXT_COLOR,
                (card_rect.centerx, question_y),
            )
            question_y += question_line_height

        options_top = question_rect.bottom + 12
        options_available = max(0, status_rect.top - options_top - 12)
        option_x = content_left
        option_width = content_width

        option_font, wrapped_options, option_heights, option_gap = self._build_option_layouts(
            max_width=option_width - 30,
            max_height=options_available,
        )

        line_height = option_font.get_height() + 4
        total_options_height = sum(option_heights) + option_gap * max(0, len(option_heights) - 1)
        option_y = options_top + max(0, (options_available - total_options_height) // 2)

        for idx, option in enumerate(self.options):
            option_rect = pygame.Rect(
                option_x,
                option_y,
                option_width,
                option_heights[idx],
            )
            option_bg, option_border = self._option_colors(idx)
            draw_pixel_panel(
                screen,
                option_rect,
                with_alpha(option_bg, 235),
                with_alpha(option_border, 255),
                border_size=3,
            )

            wrapped_lines = wrapped_options[idx]
            text_color = DARK if idx == self.selected_index and not self.answered else TEXT_COLOR
            text_block_height = len(wrapped_lines) * line_height - 4
            text_y = option_rect.y + max(8, (option_rect.height - text_block_height) // 2)
            for line in wrapped_lines:
                text_surface = option_font.render(line, False, text_color)
                screen.blit(text_surface, (option_rect.x + 14, text_y))
                text_y += line_height

            option_y += option_rect.height + option_gap

        self._draw_feedback_and_hint(screen, status_rect)

    def _fit_question_lines(self, max_width: int, max_height: int):
        for font in (self.game.font_medium, self.game.font_ui):
            line_height = font.get_height() + 4
            max_lines = max(1, max_height // max(1, line_height))
            wrapped = wrap_text(font, self.question, max_width)
            if len(wrapped) <= max_lines:
                return wrapped, font

        fallback_font = self.game.font_ui
        fallback_line_height = fallback_font.get_height() + 4
        fallback_lines = max(1, max_height // max(1, fallback_line_height))
        wrapped = wrap_text(fallback_font, self.question, max_width)
        wrapped = wrapped[:fallback_lines]
        wrapped[-1] = truncate_with_ellipsis(fallback_font, wrapped[-1], max_width)
        return wrapped, fallback_font

    def _build_option_layouts(self, max_width: int, max_height: int):
        best_layout = None
        best_overflow = float("inf")

        for font in (self.game.font_small, self.game.font_ui):
            line_height = font.get_height() + 4
            for option_gap in (10, 8, 6):
                wrapped_options: list[list[str]] = []
                option_heights: list[int] = []
                for idx, option in enumerate(self.options):
                    lines = wrap_text(font, f"{idx + 1}. {option}", max_width)
                    wrapped_options.append(lines)
                    option_heights.append(max(line_height + 16, len(lines) * line_height + 16))

                total_height = sum(option_heights) + option_gap * max(0, len(self.options) - 1)
                overflow = max(0, total_height - max_height)

                if overflow == 0:
                    return font, wrapped_options, option_heights, option_gap

                if overflow < best_overflow:
                    best_overflow = overflow
                    best_layout = (font, wrapped_options, option_heights, option_gap)

        if best_layout is None:
            line_height = self.game.font_ui.get_height() + 4
            fallback_lines = [wrap_text(self.game.font_ui, f"{idx + 1}. {option}", max_width) for idx, option in enumerate(self.options)]
            fallback_heights = [max(line_height + 16, len(lines) * line_height + 16) for lines in fallback_lines]
            return self.game.font_ui, fallback_lines, fallback_heights, 6
        return best_layout

    def _draw_feedback_and_hint(self, screen, status_rect: pygame.Rect) -> None:
        panel_fill = with_alpha(blend_color(WHITE, PRIMARY, 0.16), 232)
        panel_border = with_alpha(blend_color(PRIMARY, WHITE, 0.40), 255)

        if self.answered:
            feedback_color = SUCCESS_COLOR if self.is_correct else ERROR_COLOR
            pulse = 0.68 + 0.32 * abs(math.sin(self.feedback_time * 6.0))
            panel_fill = with_alpha(blend_color(WHITE, feedback_color, 0.22 * pulse), 238)
            panel_border = with_alpha(blend_color(PRIMARY, feedback_color, 0.40), 255)

        draw_pixel_panel(
            screen,
            status_rect,
            panel_fill,
            panel_border,
            border_size=3,
        )

        if self.answered:
            feedback_max_width = status_rect.width - 26
            headline = "CORRETO!" if self.is_correct else "ERRADO!"
            detail_font = self.game.font_ui
            details_lines = wrap_text(detail_font, self.feedback_text, feedback_max_width)
            max_detail_lines = 2
            if len(details_lines) > max_detail_lines:
                details_lines = details_lines[:max_detail_lines]
                details_lines[-1] = truncate_with_ellipsis(
                    detail_font,
                    details_lines[-1],
                    feedback_max_width,
                )

            feedback_surface = detail_font.render(headline, False, feedback_color)
            feedback_rect = feedback_surface.get_rect(center=(status_rect.centerx, status_rect.y + 28))
            screen.blit(feedback_surface, feedback_rect)

            line_height = detail_font.get_height() + 2
            details_y = status_rect.y + 56
            for line in details_lines:
                detail_surface = detail_font.render(line, False, TEXT_COLOR)
                detail_rect = detail_surface.get_rect(center=(status_rect.centerx, details_y))
                screen.blit(detail_surface, detail_rect)
                details_y += line_height
            return

        hint = self.game.font_ui.render(
            "SELECIONE UMA OPCAO E APERTE ENTER",
            False,
            blend_color(DARK, PRIMARY, 0.2),
        )
        hint_rect = hint.get_rect(center=(status_rect.centerx, status_rect.centery))
        screen.blit(hint, hint_rect)

    def _option_colors(self, index: int):
        idle_bg = blend_color(WHITE, BLUE_ACC, 0.18)
        idle_border = blend_color(PRIMARY, WHITE, 0.40)

        if not self.answered:
            if index == self.selected_index:
                selected_bg = blend_color(SELECTION_COLOR, WHITE, 0.36)
                selected_border = blend_color(SELECTION_COLOR, PRIMARY, 0.35)
                return selected_bg, selected_border
            return idle_bg, idle_border

        pulse = 0.55 + 0.45 * abs(math.sin(self.feedback_time * 7.0))
        if index == self.correct_index:
            anim_bg = blend_color(idle_bg, SUCCESS_COLOR, pulse)
            anim_border = blend_color(PRIMARY, SUCCESS_COLOR, pulse)
            return anim_bg, anim_border

        if index == self.selected_index and not self.is_correct:
            anim_bg = blend_color(idle_bg, ERROR_COLOR, pulse)
            anim_border = blend_color(PRIMARY, ERROR_COLOR, pulse)
            return anim_bg, anim_border

        if index == self.selected_index and self.is_correct:
            anim_bg = blend_color(idle_bg, SELECTION_COLOR, 0.35)
            anim_border = blend_color(PRIMARY, SELECTION_COLOR, 0.45)
            return anim_bg, anim_border

        return idle_bg, idle_border

    def _submit_answer(self) -> None:
        self.answered = True
        self.is_correct = self.selected_index == self.correct_index
        self.game.handle_quiz_result(self.node_id, self.is_correct)

        if self.is_correct:
            self.feedback_text = "NOVOS NOS FORAM DESBLOQUEADOS."
        else:
            correct_option = self.options[self.correct_index]
            self.feedback_text = (
                f"RESPOSTA: {self.correct_index + 1}. {correct_option}"
            )
            self.shake_time = 0.45
        self.feedback_time = 0.0

    def _current_shake_offset(self) -> int:
        if self.shake_time <= 0.0:
            return 0
        strength = self.shake_time / 0.45
        oscillation = math.sin(self.scene_time * 48.0)
        return int(12 * strength * oscillation)
