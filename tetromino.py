from settings import *
import random

MOVE_DIRS = {
    "left": vec(-1, 0),
    "right": vec(1, 0),
    "down": vec(0, 1),
}

# Try rotation, then small shifts if blocked (wall kick)
WALL_KICKS = (
    vec(0, 0),
    vec(-1, 0),
    vec(1, 0),
    vec(0, -1),
    vec(-1, -1),
    vec(1, -1),
    vec(-2, 0),
    vec(2, 0),
)


class Block(pg.sprite.Sprite):
    def __init__(self, tetromino, pos):
        self.tetromino = tetromino
        # position depends on whether this tetromino is the current falling piece
        base_offset = INITIAL_POS_OFFSET if tetromino.current else NEXT_POS_OFFSET
        self.pos = vec(pos) + base_offset
        self.alive = True

        if tetromino.current:
            super().__init__(tetromino.tetris.sprite_group)
        else:
            super().__init__()

        if tetromino.image is not None:
            self.image = tetromino.image.copy()
        else:
            self.image = pg.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill(TETROMINO_COLORS[tetromino.shape])
            pg.draw.rect(
                self.image,
                "orange",
                (1, 1, TILE_SIZE - 2, TILE_SIZE - 2),
                border_radius=8,
            )
        self.rect = self.image.get_rect(topleft=self.pos * TILE_SIZE)

    def rotate(self, pivot_pos):
        translated = self.pos - pivot_pos
        rotated = translated.rotate(90)
        return rotated + pivot_pos

    def set_pos(self, pos):
        # pos is an absolute position (already includes any offset); update and snap to grid
        self.pos = vec(round(pos.x), round(pos.y))
        self.rect.topleft = self.pos * TILE_SIZE

    def update(self):
        if not self.alive:
            self.kill()


class Tetromino:
    def __init__(self, tetris, current = True):
        self.tetris = tetris
        self.current = current
        self.shape = random.choice(list(TETROMINOES.keys()))
        self.image = (
            random.choice(tetris.app.images) if tetris.app.images else None
        )
        self.blocks = [Block(self, pos) for pos in TETROMINOES[self.shape]]
        self.landing = False

    def get_blocks_pos(self, direction=vec(0, 0)):
        return [block.pos + direction for block in self.blocks]

    def get_pivot(self):
        if self.shape == "O":
            xs = [b.pos.x for b in self.blocks]
            ys = [b.pos.y for b in self.blocks]
            return vec((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        if self.shape == "I":
            return self.blocks[1].pos
        return self.blocks[0].pos

    def is_valid(self, positions):
        field = self.tetris.field_array
        seen = set()
        own_blocks = set(self.blocks)

        for pos in positions:
            x, y = round(pos.x), round(pos.y)
            if (x, y) in seen:
                return False
            seen.add((x, y))

            if not (0 <= x < FIELD_W):
                return False
            if y >= FIELD_H:
                return False
            if y >= 0 and field[y][x]:
                occupant = field[y][x]
                if occupant not in own_blocks:
                    return False
        return True

    def move(self, direction):
        if isinstance(direction, str):
            direction = MOVE_DIRS.get(direction, vec(0, 0))

        new_pos = self.get_blocks_pos(direction)
        if self.is_valid(new_pos):
            if direction.y > 0:
                self.landing = False
            for block, pos in zip(self.blocks, new_pos):
                block.set_pos(pos)
            return True

        if direction.y > 0:
            self.landing = True
        return False

    def rotate(self):
        if self.shape == "O":
            return

        pivot = self.get_pivot()
        rotated = [block.rotate(pivot) for block in self.blocks]

        for kick in WALL_KICKS:
            test_pos = [pos + kick for pos in rotated]
            if self.is_valid(test_pos):
                for block, pos in zip(self.blocks, test_pos):
                    block.set_pos(pos)
                return

    def update(self):
        self.move("down")
