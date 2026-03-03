from __future__ import annotations

from typing import Sequence

import pygame
from pygame.math import Vector2

from settings import Color, ColorA, with_alpha


class PixelFont:
    """Wrapper de fonte com renderizacao pixelada via upscaling nearest-neighbor."""

    def __init__(
        self,
        size: int,
        *,
        scale: int = 3,
        family: str | None = None,
        bold: bool = False,
    ) -> None:
        self.scale = max(1, scale)
        base_size = max(6, size // self.scale)
        self.base_font = pygame.font.SysFont(family, base_size, bold=bold)

    def render(self, text: str, antialias: bool, color) -> pygame.Surface:
        _ = antialias
        base = self.base_font.render(text, False, color)
        if self.scale == 1:
            return base
        return pygame.transform.scale(base, (base.get_width() * self.scale, base.get_height() * self.scale))

    def size(self, text: str) -> tuple[int, int]:
        width, height = self.base_font.size(text)
        return width * self.scale, height * self.scale

    def get_height(self) -> int:
        return self.base_font.get_height() * self.scale


def create_pixel_sprite(
    pattern: Sequence[str],
    palette: dict[str, Color | ColorA],
    *,
    pixel_size: int = 4,
) -> pygame.Surface:
    rows = len(pattern)
    cols = max((len(row) for row in pattern), default=0)
    surface = pygame.Surface((cols * pixel_size, rows * pixel_size), pygame.SRCALPHA)

    for y, row in enumerate(pattern):
        for x, key in enumerate(row):
            if key == ".":
                continue
            color = palette.get(key)
            if color is None:
                continue
            pygame.draw.rect(
                surface,
                color,
                pygame.Rect(x * pixel_size, y * pixel_size, pixel_size, pixel_size),
            )
    return surface


def draw_pixel_panel(
    surface: pygame.Surface,
    rect: pygame.Rect | Sequence[int],
    fill_color: Color | ColorA,
    border_color: Color | ColorA,
    *,
    border_size: int = 4,
    shadow_color: Color | ColorA | None = None,
    shadow_offset: tuple[int, int] = (6, 6),
) -> None:
    box = pygame.Rect(rect)
    if shadow_color is not None:
        shadow_rect = box.move(shadow_offset)
        pygame.draw.rect(surface, shadow_color, shadow_rect)
    pygame.draw.rect(surface, fill_color, box)
    pygame.draw.rect(surface, border_color, box, width=border_size)


def draw_rounded_rect(
    surface: pygame.Surface,
    rect: pygame.Rect | Sequence[int],
    color: Color | ColorA,
    radius: int = 18,
    border_width: int = 0,
    border_color: Color | ColorA | None = None,
) -> None:
    """Compatibilidade com versao anterior."""
    rect_obj = pygame.Rect(rect)
    if rect_obj.width <= 0 or rect_obj.height <= 0:
        return

    temp = pygame.Surface(rect_obj.size, pygame.SRCALPHA)
    pygame.draw.rect(
        temp,
        color,
        pygame.Rect(0, 0, rect_obj.width, rect_obj.height),
        border_radius=radius,
    )
    if border_width > 0:
        pygame.draw.rect(
            temp,
            border_color or color,
            pygame.Rect(0, 0, rect_obj.width, rect_obj.height),
            width=border_width,
            border_radius=radius,
        )
    surface.blit(temp, rect_obj.topleft)


def draw_text_centralizado(
    surface: pygame.Surface,
    font,
    text: str,
    color: Color,
    center: tuple[float, float],
) -> pygame.Rect:
    text_surface = font.render(text, False, color)
    rect = text_surface.get_rect(center=(int(center[0]), int(center[1])))
    surface.blit(text_surface, rect)
    return rect


def wrap_text(font, text: str, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
        current = word

    if current:
        lines.append(current)
    return lines


def truncate_with_ellipsis(font, text: str, max_width: int) -> str:
    if font.size(text)[0] <= max_width:
        return text
    trimmed = text
    while trimmed and font.size(trimmed + "...")[0] > max_width:
        trimmed = trimmed[:-1]
    return trimmed + "..."


def build_vertical_gradient(
    size: tuple[int, int], top_color: Color, bottom_color: Color
) -> pygame.Surface:
    width, height = size
    gradient = pygame.Surface((width, height), pygame.SRCALPHA)
    if height <= 1:
        gradient.fill(top_color)
        return gradient

    for y in range(height):
        t = y / (height - 1)
        color = tuple(
            int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3)
        )
        pygame.draw.line(gradient, color, (0, y), (width, y))
    return gradient


def draw_glow_circle(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: Color,
    base_alpha: int = 100,
    steps: int = 5,
) -> None:
    for step in range(steps, 0, -1):
        t = step / steps
        current_radius = int(radius * t)
        alpha = int(base_alpha * (t * t))
        draw_pixel_disc(surface, center, current_radius, with_alpha(color, alpha), pixel_size=4)


def draw_node_shadow(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: Color,
    offset: tuple[int, int] = (0, 6),
) -> None:
    shadow_center = (center[0] + offset[0], center[1] + offset[1])
    for extra, alpha in ((8, 25), (4, 45)):
        draw_pixel_disc(
            surface,
            shadow_center,
            radius + extra,
            with_alpha(color, alpha),
            pixel_size=4,
        )


def draw_lock_icon(
    surface: pygame.Surface, center: tuple[int, int], color: Color, size: int = 12
) -> None:
    px = max(2, size // 6)
    cx, cy = center

    for dx in range(-2, 3):
        pygame.draw.rect(surface, color, pygame.Rect(cx + dx * px, cy + px, px, px))
        pygame.draw.rect(surface, color, pygame.Rect(cx + dx * px, cy + 2 * px, px, px))

    shackle_offsets = [(-1, -1), (0, -2), (1, -1)]
    for ox, oy in shackle_offsets:
        pygame.draw.rect(surface, color, pygame.Rect(cx + ox * px, cy + oy * px, px, px))
    pygame.draw.rect(surface, color, pygame.Rect(cx - 2 * px, cy, px, px))
    pygame.draw.rect(surface, color, pygame.Rect(cx + 2 * px, cy, px, px))


def draw_curved_connection(
    surface: pygame.Surface,
    start: tuple[int, int],
    end: tuple[int, int],
    color: Color,
    width: int = 4,
    curvature: float = 0.18,
) -> None:
    p0 = Vector2(start)
    p2 = Vector2(end)
    direction = p2 - p0
    if direction.length_squared() == 0:
        return

    midpoint = (p0 + p2) * 0.5
    perpendicular = Vector2(-direction.y, direction.x)
    if perpendicular.length_squared() > 0:
        perpendicular = perpendicular.normalize()
    bend = min(80.0, direction.length() * curvature)
    p1 = midpoint + perpendicular * bend

    points = [_quadratic_point(p0, p1, p2, i / 34.0) for i in range(35)]
    block_size = max(2, width)
    for px, py in points:
        pygame.draw.rect(
            surface,
            color,
            pygame.Rect(px - block_size // 2, py - block_size // 2, block_size, block_size),
        )


def _quadratic_point(p0: Vector2, p1: Vector2, p2: Vector2, t: float) -> tuple[int, int]:
    nt = 1.0 - t
    point = (nt * nt) * p0 + (2.0 * nt * t) * p1 + (t * t) * p2
    return int(point.x), int(point.y)


def draw_pixel_disc(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: Color | ColorA,
    *,
    pixel_size: int = 3,
) -> None:
    if radius <= 0:
        return
    cx, cy = center
    step = max(1, pixel_size)
    r2 = radius * radius
    for y in range(-radius, radius + 1, step):
        for x in range(-radius, radius + 1, step):
            if x * x + y * y <= r2:
                pygame.draw.rect(surface, color, pygame.Rect(cx + x, cy + y, step, step))


def draw_pixel_ring(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: Color | ColorA,
    *,
    thickness: int = 3,
    pixel_size: int = 3,
) -> None:
    inner = max(0, radius - thickness)
    cx, cy = center
    step = max(1, pixel_size)
    r2 = radius * radius
    inner2 = inner * inner
    for y in range(-radius, radius + 1, step):
        for x in range(-radius, radius + 1, step):
            d2 = x * x + y * y
            if inner2 <= d2 <= r2:
                pygame.draw.rect(surface, color, pygame.Rect(cx + x, cy + y, step, step))


def create_player_sprite(
    body_color: Color, accent_color: Color, eye_color: Color, dark_color: Color
) -> pygame.Surface:
    pattern = [
        "................",
        ".......22.......",
        "......2222......",
        "......2112......",
        ".....211112.....",
        ".....211112.....",
        ".....211112.....",
        ".....111111.....",
        "....31111113....",
        "...3311111133...",
        "..333111111333..",
        "..33..1111..33..",
        "..3...1111...3..",
        ".......11.......",
        ".......11.......",
        "................",
    ]
    palette: dict[str, Color | ColorA] = {
        "1": body_color,
        "2": eye_color,
        "3": accent_color,
        "4": dark_color,
    }
    sprite = create_pixel_sprite(pattern, palette, pixel_size=3)

    # Contorno escuro para destacar no mapa.
    outlined = pygame.Surface((sprite.get_width() + 6, sprite.get_height() + 6), pygame.SRCALPHA)
    for ox, oy in ((0, 0), (2, 0), (4, 0), (0, 2), (4, 2), (0, 4), (2, 4), (4, 4)):
        outline_layer = sprite.copy()
        tint = pygame.Surface(outline_layer.get_size(), pygame.SRCALPHA)
        tint.fill(with_alpha(dark_color, 255))
        outline_layer.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        outlined.blit(outline_layer, (ox, oy))
    outlined.blit(sprite, (3, 3))
    return outlined


def create_cloud_sprite(
    color_main: Color,
    color_light: Color,
    color_shadow: Color | None = None,
    *,
    pixel_size: int = 6,
) -> pygame.Surface:
    pattern = [
        "..................",
        "......11111.......",
        "...11111111111....",
        "..1111222211111...",
        ".111122222221111..",
        ".111122222221111..",
        "..1111111111111...",
        "...11111111111....",
        ".....3333333......",
        "....333333333.....",
    ]
    palette: dict[str, Color | ColorA] = {
        "1": color_main,
        "2": color_light,
    }
    if color_shadow is not None:
        palette["3"] = color_shadow
    return create_pixel_sprite(pattern, palette, pixel_size=pixel_size)
