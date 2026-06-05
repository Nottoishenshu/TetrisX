from settings import *
from tetromino import Tetromino
import pygame.freetype as ft

class Text:
    def __init__(self, app):
        self.app = app
        try:
            self.font = ft.Font(str(FONT_PATH), 24)
        except (FileNotFoundError, OSError, pg.error):
            self.font = ft.SysFont("consolas", 24)
    
    def draw(self):
        sidebar_x = int(WIN_W * 0.75)
        panel_rect = pg.Rect(sidebar_x + 8, 8, WIN_W - sidebar_x - 16, WIN_H - 16)
        pg.draw.rect(self.app.screen, (34, 44, 77), panel_rect, border_radius=20)
        pg.draw.rect(self.app.screen, (105, 174, 255), panel_rect, width=2, border_radius=20)

        x = sidebar_x + 24
        current_y = 24
        self.font.render_to(self.app.screen, (x, current_y), text="TETRISX", fgcolor="#ffd966", size=36, bgcolor=None)
        current_y += 48

        score_label = f"SCORE"
        self.font.render_to(self.app.screen, (x, current_y), text=score_label, fgcolor="#aedcff", size=22, bgcolor=None)
        current_y += 28
        self.font.render_to(self.app.screen, (x, current_y), text=f"{self.app.tetris.score}", fgcolor="#ffffff", size=28, bgcolor=None)
        current_y += 46

        # Draw NEXT piece preview section
        self.font.render_to(self.app.screen, (x, current_y), text="NEXT", fgcolor="#aedcff", size=22, bgcolor=None)
        current_y += 28

        preview_size = 28
        self._draw_next_piece(current_y, sidebar_x, preview_size)
        current_y += 68

        # Draw controls at the bottom
        bottom_y = WIN_H - 130
        self.font.render_to(self.app.screen, (x, bottom_y), text="CONTROLS", fgcolor="#b8e0ff", size=22, bgcolor=None)
        bottom_y += 30
        self.font.render_to(self.app.screen, (x, bottom_y), text="← → : Move", fgcolor="#d8eaff", size=16, bgcolor=None)
        bottom_y += 24
        self.font.render_to(self.app.screen, (x, bottom_y), text="↑ / W / X : Rotate", fgcolor="#d8eaff", size=16, bgcolor=None)
        bottom_y += 24
        self.font.render_to(self.app.screen, (x, bottom_y), text="↓ : Speed up", fgcolor="#d8eaff", size=16, bgcolor=None)

    def _draw_next_piece(self, base_y, sidebar_x, preview_size):
        if not self.app.tetris.next_tetromino:
            return

        shape = self.app.tetris.next_tetromino.shape
        shape_offsets = [vec(pos) for pos in TETROMINOES[shape]]
        
        xs = [pos.x for pos in shape_offsets]
        ys = [pos.y for pos in shape_offsets]
        shape_width = (max(xs) - min(xs) + 1) * preview_size
        shape_height = (max(ys) - min(ys) + 1) * preview_size
        
        center_x = sidebar_x + (WIN_W - sidebar_x) / 2
        origin_x = center_x - shape_width / 2 - min(xs) * preview_size
        origin_y = base_y + 8 - min(ys) * preview_size
        
        for offset, block in zip(shape_offsets, self.app.tetris.next_tetromino.blocks):
            if block.image:
                image = pg.transform.scale(block.image, (preview_size, preview_size))
                pos_x = int(origin_x + offset.x * preview_size)
                pos_y = int(origin_y + offset.y * preview_size)
                self.app.screen.blit(image, (pos_x, pos_y))


class Tetris:
    def __init__(self, app):
        self.app = app
        self.score = 0
        self.sprite_group = pg.sprite.Group()
        self.field_array = self.get_field_array()
        self.speed_up = False
        self.game_over = False
        self.spawn_tetromino()
        self.next_tetromino = Tetromino(self, current=False)

        self.score = 0
        self.lines_cleared = 0
        self.points_per_line = [0, 100, 300, 500, 800]  # Points for clearing 0, 1, 2, 3, or 4 lines

    def get_score_for_lines(self, lines_cleared):
        if 0 <= lines_cleared < len(self.points_per_line):
            return self.points_per_line[lines_cleared]
        return 0

    def get_field_array(self):
        return [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]

    def spawn_tetromino(self):
        if self.game_over:
            return

        for _ in range(20):
            tetromino = Tetromino(self)
            tetromino.landing = False
            positions = [block.pos for block in tetromino.blocks]

            if tetromino.is_valid(positions):
                self.tetromino = tetromino
                return

            for block in tetromino.blocks:
                block.kill()

        self.game_over = True

    def put_tetromino_blocks_in_array(self):
        for block in self.tetromino.blocks:
            x, y = round(block.pos.x), round(block.pos.y)
            if 0 <= y < FIELD_H and 0 <= x < FIELD_W:
                self.field_array[y][x] = block

    def check_tetromino_landing(self):
        if self.game_over or not self.tetromino.landing:
            return

        self.speed_up = False
        self.put_tetromino_blocks_in_array()
        self.check_full_lines()
        self.promote_next_tetromino()
        self.next_tetromino = Tetromino(self, current=False)

    def promote_next_tetromino(self):
        self.tetromino = self.next_tetromino
        self.tetromino.current = True
        self.tetromino.landing = False

        # Add the promoted piece's blocks to the active sprite group
        for block in self.tetromino.blocks:
            self.sprite_group.add(block)

        initial_positions = [vec(pos) + INITIAL_POS_OFFSET for pos in TETROMINOES[self.tetromino.shape]]
        if not self.tetromino.is_valid(initial_positions):
            self.game_over = True
            return

        for block, pos in zip(self.tetromino.blocks, initial_positions):
            block.set_pos(pos)

    def check_full_lines(self):
        lines_cleared = 0
        y = FIELD_H - 1
        while y >= 0:
            if all(self.field_array[y]):
                lines_cleared += 1
                for x in range(FIELD_W):
                    block = self.field_array[y][x]
                    if block:
                        block.alive = False
                        self.field_array[y][x] = 0

                for row in range(y, 0, -1):
                    self.field_array[row] = list(self.field_array[row - 1])
                    for x in range(FIELD_W):
                        block = self.field_array[row][x]
                        if block:
                            block.set_pos(vec(x, row))

                self.field_array[0] = [0] * FIELD_W
            else:
                y -= 1

        if lines_cleared:
            self.score += self.get_score_for_lines(lines_cleared)
            self.lines_cleared += lines_cleared

        return lines_cleared

    def control(self, key):
        if self.game_over:
            return

        if key == pg.K_LEFT:
            self.tetromino.move("left")
        elif key == pg.K_RIGHT:
            self.tetromino.move("right")
        elif key in (pg.K_UP, pg.K_w, pg.K_x):
            self.tetromino.rotate()
        elif key == pg.K_DOWN:
            self.tetromino.move("down")

    def draw_grid(self, surface):
        for x in range(FIELD_W):
            for y in range(FIELD_H):
                pg.draw.rect(
                    surface,
                    "black",
                    (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                    1,
                )

    def draw_next(self, surface):
        if not self.next_tetromino:
            return

        sidebar_w = int(WIN_RES[0] * 0.25)
        sidebar_x = int(WIN_RES[0]) - sidebar_w
        preview_size = int(TILE_SIZE * 0.65)
        preview_center = vec(sidebar_x + sidebar_w / 2, WIN_RES[1] * 0.25)

        font = pg.font.SysFont("consolas", 24)
        text = font.render("NEXT", True, "white")
        text_rect = text.get_rect(midtop=(sidebar_x + sidebar_w / 2, 20))
        surface.blit(text, text_rect)

        shape_offsets = [vec(pos) for pos in TETROMINOES[self.next_tetromino.shape]]
        xs = [pos.x for pos in shape_offsets]
        ys = [pos.y for pos in shape_offsets]
        shape_width = (max(xs) - min(xs) + 1) * preview_size
        shape_height = (max(ys) - min(ys) + 1) * preview_size
        origin = preview_center - vec(shape_width / 2, shape_height / 2) + vec(-min(xs) * preview_size, -min(ys) * preview_size)

        for offset, block in zip(shape_offsets, self.next_tetromino.blocks):
            image = pg.transform.scale(block.image, (preview_size, preview_size))
            pos = origin + vec(offset.x * preview_size, offset.y * preview_size)
            surface.blit(image, pos)

    def update(self):
        if self.game_over:
            return

        should_move = self.app.anim_trigger or (
            self.speed_up and self.app.fast_anim_trigger
        )
        if should_move:
            self.tetromino.update()
            self.check_tetromino_landing()
            self.sprite_group.update()

    def draw(self, surface):
        self.draw_grid(surface)
        self.sprite_group.draw(surface)

        if self.game_over:
            font = pg.font.SysFont("consolas", 36)
            text = font.render("GAME OVER", True, "white")
            rect = text.get_rect(center=(FIELD_RES[0] // 2, FIELD_RES[1] // 2))
            surface.blit(text, rect)
