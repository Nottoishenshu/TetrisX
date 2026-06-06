const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const nextCanvas = document.getElementById('next');
const nextCtx = nextCanvas.getContext('2d');
const scoreValue = document.getElementById('scoreValue');
const linesValue = document.getElementById('linesValue');
const overlay = document.getElementById('overlay');
const startButton = document.getElementById('startButton');
const restartButton = document.getElementById('restartButton');

const COLS = 10;
const ROWS = 20;
const TILE = 30;
const DROP_BASE = 800;
const POINTS = [0, 100, 300, 500, 800];

const ASSET_FILES = [
  'assets/0.piskel',
  'assets/1.piskel',
  'assets/2.piskel',
  'assets/3.piskel',
  'assets/4.piskel',
  'assets/5.piskel',
];

const SHAPE_ORDER = ['I', 'J', 'L', 'O', 'S', 'T', 'Z'];
const SHAPE_IMAGE_MAP = {};

const WALL_KICKS = [
  [0, 0],
  [-1, 0],
  [1, 0],
  [0, -1],
  [-1, -1],
  [1, -1],
  [-2, 0],
  [2, 0],
];

const COLORS = {
  I: '#3fe1ff',
  J: '#4c79ff',
  L: '#ffb85b',
  O: '#fde74c',
  S: '#40c057',
  T: '#b962ff',
  Z: '#ff5f5f',
};

const SHAPES = {
  I: [
    [-1, 0],
    [0, 0],
    [1, 0],
    [2, 0],
  ],
  J: [
    [-1, 0],
    [0, 0],
    [1, 0],
    [1, -1],
  ],
  L: [
    [-1, 0],
    [0, 0],
    [1, 0],
    [-1, -1],
  ],
  O: [
    [0, 0],
    [1, 0],
    [0, -1],
    [1, -1],
  ],
  S: [
    [0, 0],
    [1, 0],
    [-1, -1],
    [0, -1],
  ],
  T: [
    [-1, 0],
    [0, 0],
    [1, 0],
    [0, -1],
  ],
  Z: [
    [-1, 0],
    [0, 0],
    [0, -1],
    [1, -1],
  ],
};

let grid;
let currentPiece;
let nextPiece;
let score = 0;
let lines = 0;
let dropInterval = DROP_BASE;
let lastTime = 0;
let dropCounter = 0;
let running = false;
let isGameOver = false;
let blockImages = [];

startButton.disabled = true;
overlay.textContent = 'Loading sprites...';

startButton.addEventListener('click', startGame);
restartButton.addEventListener('click', startGame);

window.addEventListener('keydown', (event) => {
  if (!running) {
    return;
  }

  const key = event.key.toLowerCase();
  if (isGameOver && key === ' ') {
    startGame();
    return;
  }

  if (isGameOver) {
    return;
  }

  switch (key) {
    case 'arrowleft':
    case 'a':
      movePiece(-1, 0);
      break;
    case 'arrowright':
    case 'd':
      movePiece(1, 0);
      break;
    case 'arrowdown':
    case 's':
      dropPiece();
      break;
    case 'arrowup':
    case 'w':
    case 'x':
      rotatePiece();
      break;
    case ' ': // space hard drop
      hardDrop();
      break;
  }
});

async function loadSprites() {
  const loaded = [];

  for (const path of ASSET_FILES) {
    try {
      const response = await fetch(path);
      if (!response.ok) {
        continue;
      }
      const data = await response.json();
      const layers = data?.piskel?.layers;
      if (!layers?.length) {
        continue;
      }
      const layer = typeof layers[0] === 'string' ? JSON.parse(layers[0]) : layers[0];
      const chunk = layer?.chunks?.[0];
      const base64PNG = chunk?.base64PNG;
      if (!base64PNG) {
        continue;
      }

      const imageData = base64PNG.startsWith('data:image/png;base64,')
        ? base64PNG
        : `data:image/png;base64,${base64PNG}`;

      const img = new Image();
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = imageData;
      });
      loaded.push(img);
    } catch (error) {
      console.warn('Failed to load sprite', path, error);
    }
  }

  if (loaded.length > 0) {
    SHAPE_ORDER.forEach((shape, index) => {
      SHAPE_IMAGE_MAP[shape] = loaded[index % loaded.length];
    });
  }

  return loaded;
}

function createGrid() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(null));
}

function createPiece() {
  const shapeKeys = Object.keys(SHAPES);
  const shape = shapeKeys[Math.floor(Math.random() * shapeKeys.length)];
  return {
    shape,
    coords: SHAPES[shape].map(([x, y]) => [x, y]),
    color: COLORS[shape],
    image: SHAPE_IMAGE_MAP[shape] || (blockImages.length ? blockImages[Math.floor(Math.random() * blockImages.length)] : null),
  };
}

function startGame() {
  grid = createGrid();
  score = 0;
  lines = 0;
  dropInterval = DROP_BASE;
  isGameOver = false;
  running = true;
  overlay.textContent = 'Good luck!';
  overlay.style.opacity = '0.9';
  nextPiece = createPiece();
  spawnPiece();
  updateScore();
  updateLines();
  requestAnimationFrame(update);
}

function spawnPiece() {
  currentPiece = nextPiece || createPiece();
  currentPiece.x = 4;
  currentPiece.y = 0;
  nextPiece = createPiece();

  if (!pieceFits(currentPiece, 0, 0, currentPiece.coords)) {
    endGame();
  }
}

function pieceFits(piece, dx, dy, coords) {
  return coords.every(([cx, cy]) => {
    const x = piece.x + cx + dx;
    const y = piece.y + cy + dy;
    if (x < 0 || x >= COLS || y >= ROWS) {
      return false;
    }
    if (y < 0) {
      return true;
    }
    return !grid[y][x];
  });
}

function movePiece(dx, dy) {
  if (!currentPiece || !pieceFits(currentPiece, dx, dy, currentPiece.coords)) {
    return;
  }
  currentPiece.x += dx;
  currentPiece.y += dy;
}

function rotatePiece() {
  if (!currentPiece || currentPiece.shape === 'O') {
    return;
  }

  const pivot = getPivot(currentPiece);
  const rotatedCoords = currentPiece.coords.map(([x, y]) => {
    const translatedX = x - pivot.x;
    const translatedY = y - pivot.y;
    return [translatedY + pivot.x, -translatedX + pivot.y];
  });

  for (const [kickX, kickY] of WALL_KICKS) {
    const testCoords = rotatedCoords.map(([x, y]) => [x + kickX, y + kickY]);
    if (pieceFits(currentPiece, 0, 0, testCoords)) {
      currentPiece.coords = testCoords;
      return;
    }
  }
}

function dropPiece() {
  if (!currentPiece) {
    return;
  }

  if (pieceFits(currentPiece, 0, 1, currentPiece.coords)) {
    currentPiece.y += 1;
  } else {
    lockPiece();
    clearLines();
    spawnPiece();
  }
  dropCounter = 0;
}

function getPivot(piece) {
  if (piece.shape === 'I') {
    return { x: piece.coords[1][0], y: piece.coords[1][1] };
  }
  return { x: piece.coords[0][0], y: piece.coords[0][1] };
}

function hardDrop() {
  while (currentPiece && pieceFits(currentPiece, 0, 1, currentPiece.coords)) {
    currentPiece.y += 1;
  }
  if (currentPiece) {
    lockPiece();
    clearLines();
    spawnPiece();
  }
  dropCounter = 0;
}

function lockPiece() {
  currentPiece.coords.forEach(([cx, cy]) => {
    const x = currentPiece.x + cx;
    const y = currentPiece.y + cy;
    if (y >= 0 && y < ROWS && x >= 0 && x < COLS) {
      grid[y][x] = {
        color: currentPiece.color,
        image: currentPiece.image,
      };
    }
  });
}

function clearLines() {
  let removed = 0;
  for (let y = ROWS - 1; y >= 0; y -= 1) {
    if (grid[y].every((cell) => cell !== null)) {
      grid.splice(y, 1);
      grid.unshift(Array(COLS).fill(null));
      removed += 1;
      y += 1;
    }
  }

  if (removed > 0) {
    score += POINTS[removed] || removed * 200;
    lines += removed;
    dropInterval = Math.max(100, DROP_BASE - lines * 15);
    updateScore();
    updateLines();
  }
}

function endGame() {
  isGameOver = true;
  overlay.textContent = 'Game Over — press Restart or Space';
  overlay.style.opacity = '0.92';
}

function updateScore() {
  scoreValue.textContent = score;
}

function updateLines() {
  linesValue.textContent = lines;
}

function update(time = 0) {
  if (!running) {
    return;
  }

  const delta = time - lastTime;
  lastTime = time;
  dropCounter += delta;

  if (dropCounter > dropInterval && !isGameOver) {
    dropPiece();
  }

  draw();

  if (!isGameOver) {
    requestAnimationFrame(update);
  }
}

function draw() {
  ctx.fillStyle = '#08121d';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  drawGrid(ctx, canvas.width, canvas.height);
  drawBoard(ctx);

  if (currentPiece) {
    drawPiece(ctx, currentPiece);
  }

  drawNext();
}

function drawGrid(context) {
  context.strokeStyle = '#142c4f';
  context.lineWidth = 1;
  for (let x = 0; x <= COLS; x += 1) {
    context.beginPath();
    context.moveTo(x * TILE, 0);
    context.lineTo(x * TILE, canvas.height);
    context.stroke();
  }
  for (let y = 0; y <= ROWS; y += 1) {
    context.beginPath();
    context.moveTo(0, y * TILE);
    context.lineTo(canvas.width, y * TILE);
    context.stroke();
  }
}

function drawBoard(context) {
  grid.forEach((row, y) => {
    row.forEach((cell, x) => {
      if (cell) {
        drawCell(context, x, y, cell);
      }
    });
  });
}

function drawPiece(context, piece) {
  piece.coords.forEach(([cx, cy]) => {
    const x = piece.x + cx;
    const y = piece.y + cy;
    drawCell(context, x, y, piece);
  });
}

function drawCell(context, x, y, cell) {
  const px = x * TILE;
  const py = y * TILE;

  if (cell?.image) {
    context.drawImage(cell.image, px + 1, py + 1, TILE - 2, TILE - 2);
  } else {
    context.fillStyle = cell?.color || '#ffffff';
    context.fillRect(px + 2, py + 2, TILE - 4, TILE - 4);
  }

  context.strokeStyle = '#12223b';
  context.lineWidth = 2;
  context.strokeRect(px + 2, py + 2, TILE - 4, TILE - 4);
}

function drawNext() {
  nextCtx.fillStyle = '#08121d';
  nextCtx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
  nextCtx.strokeStyle = '#142c4f';
  nextCtx.strokeRect(0, 0, nextCanvas.width, nextCanvas.height);

  if (!nextPiece) {
    return;
  }

  const previewTile = 30;
  const centerX = nextCanvas.width / 2;
  const centerY = nextCanvas.height / 2;
  const offsets = nextPiece.coords;
  const minX = Math.min(...offsets.map(([x]) => x));
  const maxX = Math.max(...offsets.map(([x]) => x));
  const minY = Math.min(...offsets.map(([, y]) => y));
  const maxY = Math.max(...offsets.map(([, y]) => y));
  const dispWidth = (maxX - minX + 1) * previewTile;
  const dispHeight = (maxY - minY + 1) * previewTile;
  const offsetX = centerX - dispWidth / 2 - minX * previewTile;
  const offsetY = centerY - dispHeight / 2 - minY * previewTile;

  nextPiece.coords.forEach(([cx, cy]) => {
    const px = offsetX + cx * previewTile;
    const py = offsetY + cy * previewTile;
    if (nextPiece.image) {
      nextCtx.drawImage(nextPiece.image, px + 1, py + 1, previewTile - 2, previewTile - 2);
    } else {
      nextCtx.fillStyle = nextPiece.color;
      nextCtx.fillRect(px + 2, py + 2, previewTile - 4, previewTile - 4);
    }
    nextCtx.strokeStyle = '#12223b';
    nextCtx.lineWidth = 2;
    nextCtx.strokeRect(px + 2, py + 2, previewTile - 4, previewTile - 4);
  });
}

loadSprites().then((images) => {
  blockImages = images;
  startButton.disabled = false;
  overlay.textContent = images.length
    ? 'Sprites loaded. Press Start to play.'
    : 'Sprite load failed. Press Start to play.';
});
overlay.style.opacity = '0.9';
