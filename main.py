import base64
import io
import json
import os
import sys
import pygame as pg
import pygame.freetype as ft
from flask import Flask

app = Flask(__name__)  # Ensure this is named 'app'
from settings import *
from tetris import Tetris, Text


def load_piskel_surface(path):
    """Load a pygame surface from a .piskel file (embedded base64 PNG)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        layers = data.get("piskel", {}).get("layers", [])
        if not layers:
            return None

        layer = json.loads(layers[0]) if isinstance(layers[0], str) else layers[0]
        chunks = layer.get("chunks", [])
        if not chunks:
            return None

        b64_png = chunks[0].get("base64PNG", "")
        if "," in b64_png:
            b64_png = b64_png.split(",", 1)[1]

        png_bytes = base64.b64decode(b64_png)
        return pg.image.load(io.BytesIO(png_bytes)).convert_alpha()
    except (json.JSONDecodeError, KeyError, OSError, pg.error) as exc:
        print(f"Warning: could not load {path.name}: {exc}")
        return None


def load_block_images():
    """Load all block sprites from assets/ (.png and .piskel)."""
    if not ASSETS_DIR.is_dir():
        print(f"Warning: assets folder not found at {ASSETS_DIR}")
        return []

    images = []

    for file in sorted(ASSETS_DIR.rglob("*.png")):
        try:
            surface = pg.image.load(file).convert_alpha()
            images.append(pg.transform.scale(surface, (TILE_SIZE, TILE_SIZE)))
        except pg.error as exc:
            print(f"Warning: could not load {file.name}: {exc}")

    for file in sorted(ASSETS_DIR.glob("*.piskel")):
        surface = load_piskel_surface(file)
        if surface is not None:
            images.append(pg.transform.scale(surface, (TILE_SIZE, TILE_SIZE)))

    return images


def load_game_font(size, bold=False):
    for path in (FONT_PATH, ALT_FONT_PATH):
        try:
            return ft.Font(str(path), size)
        except (FileNotFoundError, OSError, pg.error):
            continue
    return ft.SysFont("consolas", size, bold=bold)


class Menu:
    def __init__(self, app):
        self.app = app
        self.options = ["Start Game", "Quit"]
        self.selected_index = 0
        self.title_font = load_game_font(64, bold=True)
        self.option_font = load_game_font(32)
        self.instruction_font = load_game_font(18)

    def draw(self, surface):
        surface.fill((12, 22, 54))

        card_rect = pg.Rect(40, 40, WIN_RES[0] - 80, WIN_RES[1] - 80)
        pg.draw.rect(surface, (20, 40, 95), card_rect, border_radius=24)
        pg.draw.rect(surface, (48, 118, 210), card_rect.inflate(-10, -10), width=4, border_radius=24)

        title, title_rect = self.title_font.render("TetrisX", "#ffdf4d")
        title_shadow, shadow_rect = self.title_font.render("TetrisX", "#1a1a2e")
        title_rect.center = (WIN_RES[0] / 2, WIN_RES[1] * 0.22)
        shadow_rect.center = title_rect.center
        surface.blit(title_shadow, shadow_rect.move(4, 4))
        surface.blit(title, title_rect)

        subtitle, subtitle_rect = self.instruction_font.render("Retro block puzzle", "#d8eaff")
        subtitle_rect.center = (WIN_RES[0] / 2, WIN_RES[1] * 0.31)
        surface.blit(subtitle, subtitle_rect)

        for index, option in enumerate(self.options):
            option_y = WIN_RES[1] * 0.48 + index * 60
            option_rect = pg.Rect(WIN_RES[0] * 0.23, option_y - 18, WIN_RES[0] * 0.54, 48)
            if index == self.selected_index:
                pg.draw.rect(surface, (255, 205, 84), option_rect, border_radius=16)
                text_color = "#0f1d3a"
            else:
                text_color = "#f5f5f5"
            text_surface, text_rect = self.option_font.render(option, text_color)
            text_rect.center = (WIN_RES[0] / 2, option_y + 6)
            surface.blit(text_surface, text_rect)

        hint, hint_rect = self.instruction_font.render("Use ↑/↓ or W/S to move • Enter to select", "#cbd5ff")
        hint_rect.center = (WIN_RES[0] / 2, WIN_RES[1] * 0.82)
        surface.blit(hint, hint_rect)

        if self.app.tetris and self.app.tetris.game_over:
            over_text, over_rect = self.instruction_font.render("Game over! Start a new game to play again.", "#ffb3b3")
            over_rect.center = (WIN_RES[0] / 2, WIN_RES[1] * 0.72)
            surface.blit(over_text, over_rect)

    def navigate(self, direction):
        self.selected_index = (self.selected_index + direction) % len(self.options)

    def select(self):
        option = self.options[self.selected_index]
        if option == "Start Game":
            self.app.start_game()
        elif option == "Quit":
            pg.quit()
            sys.exit()


class App:
    def __init__(self):
        pg.init()
        pg.display.set_caption("TetrisX")
        self.screen = pg.display.set_mode((int(WIN_RES[0]), int(WIN_RES[1])))
        self.clock = pg.time.Clock()
        self.field_surface = pg.Surface(FIELD_RES)
        self.anim_trigger = False
        self.fast_anim_trigger = False
        self.set_timer()
        self.images = load_block_images()
        self.tetris = Tetris(self)
        self.text = Text(self)
        self.menu = Menu(self)
        self.state = "menu"

    def set_timer(self):
        self.user_event = pg.USEREVENT
        self.fast_user_event = pg.USEREVENT + 1
        pg.time.set_timer(self.user_event, ANIM_TIME_INTERVAL)
        pg.time.set_timer(self.fast_user_event, FAST_ANIM_TIME_INTERVAL)

    def start_game(self):
        self.tetris = Tetris(self)
        self.menu.selected_index = 0
        self.state = "playing"

    def update(self):
        if self.state == "playing":
            self.tetris.update()
        self.clock.tick(FPS)


    def draw(self):
        if self.state == "menu":
            self.menu.draw(self.screen)
            pg.display.flip()
            return

        # Draw playfield (scaled) to the window
        self.screen.fill(BG_COLOR)
        self.field_surface.fill(FIELD_COLOR)
        self.tetris.draw(self.field_surface)

        # Reserve a sidebar on the right and scale the playfield to the remaining width
        sidebar_w = int(WIN_RES[0] * 0.25)
        playfield_w = int(WIN_RES[0]) - sidebar_w
        scaled_field = pg.transform.scale(self.field_surface, (playfield_w, int(WIN_RES[1])))
        self.screen.blit(scaled_field, (0, 0))

        # Sidebar background (right side)
        sidebar_rect = (playfield_w, 0, sidebar_w, int(WIN_RES[1]))
        pg.draw.rect(self.screen, (35, 35, 35), sidebar_rect)
        self.text.draw()

        pg.display.flip()

    def check_events(self):
        self.anim_trigger = False
        self.fast_anim_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ):
                pg.quit()
                sys.exit()

            if self.state == "menu":
                if event.type == pg.KEYDOWN:
                    if event.key in (pg.K_UP, pg.K_w):
                        self.menu.navigate(-1)
                    elif event.key in (pg.K_DOWN, pg.K_s):
                        self.menu.navigate(1)
                    elif event.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
                        self.menu.select()
                continue

            if self.state == "playing":
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_DOWN:
                        self.tetris.speed_up = True
                    self.tetris.control(event.key)
                    if self.tetris.game_over and event.key in (pg.K_RETURN, pg.K_SPACE):
                        self.state = "menu"
                elif event.type == pg.KEYUP:
                    if event.key == pg.K_DOWN:
                        self.tetris.speed_up = False
                elif event.type == self.user_event:
                    self.anim_trigger = True
                elif event.type == self.fast_user_event:
                    self.fast_anim_trigger = True

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    app = App()
    app.run()
