import pathlib

import pygame as pg

vec = pg.math.Vector2

BASE_DIR = pathlib.Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

FPS = 60
FIELD_COLOR = (48, 39, 32)
BG_COLOR = (24, 89, 117)

SPRIT_DIR_PATH = ASSETS_DIR / "sprites"
FONT_PATH = BASE_DIR / "ARCADECLASSIC.TTF"
ALT_FONT_PATH = ASSETS_DIR / "font" / "ARCADECLASSIC.TTF"

ANIM_TIME_INTERVAL = 150
FAST_ANIM_TIME_INTERVAL = 50

TILE_SIZE = 40

FIELD_W, FIELD_H = 10, 20
FIELD_RES = FIELD_W * TILE_SIZE, FIELD_H * TILE_SIZE

FIELD_SCALE, FIELD_SCALE_H = 1.7, 1.0
WIN_RES = WIN_W, WIN_H = FIELD_RES[0] * FIELD_SCALE, FIELD_RES[1] * FIELD_SCALE_H
INITIAL_POS_OFFSET = vec(FIELD_W // 2 -1 , 0)
NEXT_POS_OFFSET = vec(FIELD_W * 1.3, FIELD_H * 0.45)
MOVE_DIRECTIONS = {
    "left": vec(-1, 0),
    "right": vec(1, 0),
    "down": vec(0, 1)
}

TETROMINOES = {
    "T": [(0, 0), (-1, 0), (1, 0), (0, -1)],
    "O": [(0, 0), (0, -1), (1, 0), (1, -1)],
    "J": [(0, 0), (-1, 0), (0, -1), (0, -2)],
    "L": [(0, 0), (1, 0), (0, -1), (0, -2)],
    "I": [(0, 0), (-1, 0), (1, 0), (2, 0)],
    "S": [(0, 0), (1, 0), (0, -1), (-1, -1)],
    "Z": [(0, 0), (-1, 0), (0, -1), (1, -1)],
}

TETROMINO_COLORS = {
    "T": "purple",
    "O": "yellow",
    "J": "blue",
    "L": "orange",
    "I": "cyan",
    "S": "green",
    "Z": "red",
}
