import curses
import random
import time
from dataclasses import dataclass


# Board size
WIDTH = 10
HEIGHT = 20


# Tetromino definitions using 4x4 matrices with 'X' blocks
RAW_SHAPES = {
    "I": [
        "....",
        "XXXX",
        "....",
        "....",
    ],
    "J": [
        "X..",
        "XXX",
        "...",
    ],
    "L": [
        "..X",
        "XXX",
        "...",
    ],
    "O": [
        ".XX.",
        ".XX.",
        "....",
        "....",
    ],
    "S": [
        ".XX",
        "XX.",
        "...",
    ],
    "T": [
        ".X.",
        "XXX",
        "...",
    ],
    "Z": [
        "XX.",
        ".XX",
        "...",
    ],
}


def normalize(shape_rows):
    # Ensure 4x4 matrix for simpler rotation logic
    h = len(shape_rows)
    w = max(len(r) for r in shape_rows)
    grid = [list(r.ljust(w, ".")) for r in shape_rows]
    # pad to 4x4
    while len(grid) < 4:
        grid.append(["."] * w)
    for i in range(len(grid)):
        if len(grid[i]) < 4:
            grid[i] = grid[i] + ["."] * (4 - len(grid[i]))
    # cut or pad to 4 columns
    grid = [row[:4] for row in grid[:4]]
    return ["".join(row) for row in grid]


def rotate90(grid_rows):
    grid = [list(r) for r in grid_rows]
    n = len(grid)
    # transpose + reverse rows
    rotated = [[grid[n - j - 1][i] for j in range(n)] for i in range(n)]
    return ["".join(row) for row in rotated]


def to_coords(grid_rows):
    coords = []
    for y, row in enumerate(grid_rows):
        for x, ch in enumerate(row):
            if ch == "X":
                coords.append((x, y))
    return coords


def build_rotations(base_rows):
    base = normalize(base_rows)
    rots = []
    seen = set()
    cur = base
    for _ in range(4):
        key = tuple(cur)
        if key not in seen:
            seen.add(key)
            rots.append(to_coords(cur))
        cur = rotate90(cur)
    return rots


SHAPES = {name: build_rotations(rows) for name, rows in RAW_SHAPES.items()}


COLORS = {
    "I": 6,  # cyan
    "J": 4,  # blue
    "L": 3,  # yellow-ish
    "O": 2,  # green
    "S": 10, # bright green if available
    "T": 5,  # magenta
    "Z": 1,  # red
}


@dataclass
class Piece:
    kind: str
    rot: int
    x: int
    y: int

    @property
    def coords(self):
        return SHAPES[self.kind][self.rot]


def new_piece():
    kind = random.choice(list(SHAPES.keys()))
    rot = 0
    # spawn near top, centered
    x = WIDTH // 2 - 2
    y = -1  # allow first move to drop into view
    return Piece(kind, rot, x, y)


def can_move(board, piece: Piece, dx: int, dy: int, drot: int = 0) -> bool:
    rot = (piece.rot + drot) % len(SHAPES[piece.kind])
    for cx, cy in SHAPES[piece.kind][rot]:
        nx = piece.x + dx + cx
        ny = piece.y + dy + cy
        if nx < 0 or nx >= WIDTH:
            return False
        if ny >= HEIGHT:
            return False
        if ny >= 0 and board[ny][nx] != 0:
            return False
    return True


def lock_piece(board, piece: Piece):
    color = COLORS.get(piece.kind, 7)
    for cx, cy in piece.coords:
        x = piece.x + cx
        y = piece.y + cy
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            board[y][x] = color


def clear_lines(board):
    lines = 0
    new_rows = []
    for row in board:
        if all(cell != 0 for cell in row):
            lines += 1
        else:
            new_rows.append(row)
    for _ in range(lines):
        new_rows.insert(0, [0] * WIDTH)
    # mutate original
    for y in range(HEIGHT):
        board[y] = new_rows[y]
    return lines


def draw_board(win, board, offset_y, offset_x):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = board[y][x]
            if cell:
                try:
                    win.attron(curses.color_pair(cell))
                except curses.error:
                    pass
                win.addstr(offset_y + y, offset_x + x * 2, "██")
                try:
                    win.attroff(curses.color_pair(cell))
                except curses.error:
                    pass
            else:
                win.addstr(offset_y + y, offset_x + x * 2, "  ")


def draw_piece(win, piece: Piece, offset_y, offset_x):
    color = COLORS.get(piece.kind, 7)
    try:
        win.attron(curses.color_pair(color))
    except curses.error:
        pass
    for cx, cy in piece.coords:
        x = piece.x + cx
        y = piece.y + cy
        if y >= 0:
            win.addstr(offset_y + y, offset_x + x * 2, "██")
    try:
        win.attroff(curses.color_pair(color))
    except curses.error:
        pass


def draw_frame(stdscr, board, piece, next_piece, score, level, lines):
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    board_w = WIDTH * 2
    board_h = HEIGHT
    total_w = board_w + 2 + 18
    total_h = max(board_h + 2, 24)

    start_y = max((max_y - total_h) // 2, 0)
    start_x = max((max_x - total_w) // 2, 0)

    # Draw borders
    # Game area frame
    for y in range(board_h + 2):
        stdscr.addstr(start_y + y, start_x, "│" if 0 < y < board_h + 1 else "┌" if y == 0 else "└")
        stdscr.addstr(start_y + y, start_x + 1 + board_w, "│" if 0 < y < board_h + 1 else "┐" if y == 0 else "┘")
    for x in range(board_w):
        stdscr.addstr(start_y, start_x + 1 + x, "─")
        stdscr.addstr(start_y + 1 + board_h, start_x + 1 + x, "─")

    # Draw board and current piece
    draw_board(stdscr, board, start_y + 1, start_x + 1)
    if piece:
        draw_piece(stdscr, piece, start_y + 1, start_x + 1)

    # Sidebar
    sx = start_x + board_w + 3
    sy = start_y + 1
    stdscr.addstr(sy, sx, "TETRIS")
    stdscr.addstr(sy + 2, sx, f"Score: {score}")
    stdscr.addstr(sy + 3, sx, f"Level: {level}")
    stdscr.addstr(sy + 4, sx, f"Lines: {lines}")
    stdscr.addstr(sy + 6, sx, "Next:")

    # Draw next piece miniature
    if next_piece:
        np = Piece(next_piece.kind, 0, 0, 0)
        for cx, cy in SHAPES[np.kind][0]:
            stdscr.addstr(sy + 8 + cy, sx + cx * 2, "██", curses.color_pair(COLORS[np.kind]))

    stdscr.addstr(sy + 13, sx, "Controls:")
    stdscr.addstr(sy + 14, sx, "←/→ move, ↓ soft drop")
    stdscr.addstr(sy + 15, sx, "↑ rotate, SPACE hard drop")
    stdscr.addstr(sy + 16, sx, "p pause, q quit")

    stdscr.refresh()


def game(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    # Colors
    if curses.has_colors():
        curses.start_color()
        # Safe fallbacks; terminal may not support >7
        for i in range(1, 16):
            try:
                curses.init_pair(i, i % 8, 0)
            except curses.error:
                try:
                    curses.init_pair(i, i % 7 + 1, 0)
                except curses.error:
                    pass

    board = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
    current = new_piece()
    next_p = new_piece()
    score = 0
    level = 1
    total_lines = 0

    gravity = 0.6  # seconds per cell
    last_fall = time.time()
    last_input = 0.0
    game_over = False

    while True:
        now = time.time()

        # Input
        key = stdscr.getch()
        if key != -1:
            last_input = now
        if key in (ord("q"), ord("Q")):
            break
        if game_over:
            if key in (ord("r"), ord("R")):
                # Restart
                board = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
                current = new_piece()
                next_p = new_piece()
                score = 0
                level = 1
                total_lines = 0
                gravity = 0.6
                game_over = False
            draw_frame(stdscr, board, None, current, score, level, total_lines)
            stdscr.addstr(1, 2, "Game Over — press R to restart or Q to quit")
            stdscr.refresh()
            time.sleep(0.05)
            continue

        if key in (ord("p"), ord("P")):
            stdscr.addstr(0, 2, "Paused — press any key…")
            stdscr.nodelay(False)
            stdscr.getch()
            stdscr.nodelay(True)
            last_fall = time.time()

        moved = False
        if key == curses.KEY_LEFT and can_move(board, current, -1, 0):
            current.x -= 1
            moved = True
        elif key == curses.KEY_RIGHT and can_move(board, current, 1, 0):
            current.x += 1
            moved = True
        elif key == curses.KEY_UP and can_move(board, current, 0, 0, drot=1):
            current.rot = (current.rot + 1) % len(SHAPES[current.kind])
            moved = True
        elif key == curses.KEY_DOWN and can_move(board, current, 0, 1):
            current.y += 1
            score += 1  # soft drop point
            moved = True
        elif key == ord(" "):
            # hard drop
            dist = 0
            while can_move(board, current, 0, 1):
                current.y += 1
                dist += 1
            score += 2 * dist
            moved = True
            # Immediately lock after hard drop
            lock_piece(board, current)
            lines = clear_lines(board)
            if lines:
                total_lines += lines
                score += (0, 100, 300, 500, 800)[lines]
                if total_lines // 10 + 1 > level:
                    level = total_lines // 10 + 1
                    gravity = max(0.08, gravity * 0.85)
            current = next_p
            next_p = new_piece()
            if not can_move(board, current, 0, 0):
                game_over = True

        if now - last_fall >= gravity:
            last_fall = now
            if can_move(board, current, 0, 1):
                current.y += 1
            else:
                lock_piece(board, current)
                lines = clear_lines(board)
                if lines:
                    total_lines += lines
                    score += (0, 100, 300, 500, 800)[lines]
                    if total_lines // 10 + 1 > level:
                        level = total_lines // 10 + 1
                        gravity = max(0.08, gravity * 0.85)
                current = next_p
                next_p = new_piece()
                if not can_move(board, current, 0, 0):
                    game_over = True

        draw_frame(stdscr, board, None if game_over else current, next_p, score, level, total_lines)
        if game_over:
            stdscr.addstr(1, 2, "Game Over — press R to restart or Q to quit")
        stdscr.refresh()
        time.sleep(0.01)


def main():
    curses.wrapper(game)


if __name__ == "__main__":
    main()
