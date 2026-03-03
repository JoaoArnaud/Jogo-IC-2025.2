from __future__ import annotations

from typing import Tuple

Color = Tuple[int, int, int]
ColorA = Tuple[int, int, int, int]


def hex_to_rgb(hex_color: str) -> Color:
    """Converte '#RRGGBB' para RGB."""
    value = hex_color.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Cor hexadecimal invalida: {hex_color}")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def blend_color(color_a: Color, color_b: Color, t: float) -> Color:
    """Interpolacao linear entre duas cores RGB."""
    clamped = max(0.0, min(1.0, t))
    return tuple(
        int(color_a[i] + (color_b[i] - color_a[i]) * clamped) for i in range(3)
    )


def with_alpha(color: Color, alpha: int) -> ColorA:
    return (color[0], color[1], color[2], max(0, min(255, alpha)))


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
WINDOW_TITLE = "DeepMind Quiz"

# Paleta obrigatoria
PRIMARY_HEX = "#522a8e"
YELLOW_ACC_HEX = "#ffe400"
PINK_ACC_HEX = "#ffa7bb"
BLUE_ACC_HEX = "#a5dbff"
WHITE_HEX = "#f8f8f8"
DARK_HEX = "#1a1a1a"

PRIMARY = hex_to_rgb(PRIMARY_HEX)
YELLOW_ACC = hex_to_rgb(YELLOW_ACC_HEX)
PINK_ACC = hex_to_rgb(PINK_ACC_HEX)
BLUE_ACC = hex_to_rgb(BLUE_ACC_HEX)
WHITE = hex_to_rgb(WHITE_HEX)
DARK = hex_to_rgb(DARK_HEX)

# Variacoes suaves derivadas da paleta
BACKGROUND_TOP = blend_color(PRIMARY, WHITE, 0.14)
BACKGROUND_BOTTOM = blend_color(PRIMARY, DARK, 0.30)
EDGE_COLOR = blend_color(BLUE_ACC, PRIMARY, 0.45)
EDGE_SHADOW = blend_color(DARK, PRIMARY, 0.15)
TEXT_COLOR = blend_color(DARK, WHITE, 0.12)
PANEL_COLOR = blend_color(PRIMARY, WHITE, 0.72)
PANEL_BORDER = blend_color(PRIMARY, WHITE, 0.38)
NODE_LOCKED = blend_color(PRIMARY, WHITE, 0.50)
NODE_UNLOCKED = BLUE_ACC
NODE_COMPLETED = blend_color(BLUE_ACC, YELLOW_ACC, 0.58)
NODE_HOVER = YELLOW_ACC
GLOW_COLOR = BLUE_ACC
SELECTION_COLOR = YELLOW_ACC
SUCCESS_COLOR = blend_color(BLUE_ACC, YELLOW_ACC, 0.60)
ERROR_COLOR = blend_color(PINK_ACC, DARK, 0.32)

NODE_RADIUS = 20
PLAYER_OFFSET_Y = 42
PLAYER_MOVE_DURATION = 0.30
PLAYER_MOVE_COOLDOWN = 0.12

SCENE_FADE_SPEED = 820.0
OVERWORLD_ENTRY_FADE_SPEED = 430.0

QUIZ_CARD_WIDTH = 760
QUIZ_CARD_HEIGHT = 500
