from __future__ import annotations
from typing import Optional

from pyray import Color, color_from_hsv, get_time

from .models import Hub, MapData


def to_byte(c: float) -> int:
    if c <= 1.0:
        return int(c * 255)
    return int(c)


def get_rainbow_color(speed: float = 60.0) -> Color:
    hue = (get_time() * speed) % 360
    return color_from_hsv(hue, 1.0, 1.0)
