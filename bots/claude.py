import os
import sys
import random
from pathlib import Path

# Set to False to disable the pygame window entirely (pygame is then never imported).
ENABLE_VIEWER = False

# pygame prints a banner to stdout on import, but stdout is the protocol channel.
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

SIZE = 10
SHIPS = {"Carrier": 5, "Battleship": 4, "Destroyer": 3, "Submarine": 3, "PatrolBoat": 2}
BOT_NAME = Path(__file__).stem

BG = (30, 30, 35)
GRID_BG = (45, 45, 52)
LINE = (70, 70, 80)
TEXT = (235, 235, 240)
DIM = (170, 170, 180)
HIT = (220, 50, 50)
SUNK = (140, 30, 30)
MISS = (100, 180, 255)
BLOCKED = (20, 20, 20)
HOT = (255, 170, 40)


class Viewer:
    """The bot's own pygame window: its knowledge, heatmap and decision."""

    CELL = 36
    MARGIN = 20
    TOP = 78
    PANEL_H = 110

    def __init__(self, title):
        import pygame

        self.pg = pygame
        pos = os.environ.get("BOT_WINDOW_POS")
        if pos:
            os.environ["SDL_VIDEO_WINDOW_POS"] = pos
        pygame.display.init()
        pygame.font.init()
        width = self.MARGIN * 2 + SIZE * self.CELL
        height = self.TOP + SIZE * self.CELL + self.PANEL_H
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.title_font = pygame.font.SysFont("arial", 20, bold=True)
        self.font = pygame.font.SysFont("arial", 15)
        self.num_font = pygame.font.SysFont("arial", 11)
        self.alive = True

    def draw(self, board, score, move, mode, remaining, status):
        pg = self.pg
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # Closing the window only closes the viewer; the bot keeps playing.
                self.alive = False
                pg.display.quit()
                return

        cell, mx, top = self.CELL, self.MARGIN, self.TOP
        self.screen.fill(BG)

        self.screen.blit(self.title_font.render(f"{BOT_NAME}  |  {mode}", True, TEXT), (mx, 10))
        self.screen.blit(
            self.font.render("numbers = % of total shot likelihood", True, DIM), (mx, 34)
        )

        unknown = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == " "]
        total = sum(score[r][c] for r, c in unknown) or 1.0
        max_score = max((score[r][c] for r, c in unknown), default=0.0)

        # Column letters / row numbers
        for i in range(SIZE):
            letter = self.num_font.render(chr(ord("A") + i), True, DIM)
            self.screen.blit(letter, letter.get_rect(center=(mx + i * cell + cell // 2, top - 10)))
            number = self.num_font.render(str(i + 1), True, DIM)
            self.screen.blit(number, number.get_rect(midright=(mx - 4, top + i * cell + cell // 2)))

        for r in range(SIZE):
            for c in range(SIZE):
                rect = pg.Rect(mx + c * cell, top + r * cell, cell, cell)
                v = board[r][c]
                color = GRID_BG
                t = 0.0
                if v == "M":
                    color = MISS
                elif v == "H":
                    color = HIT
                elif v == "S":
                    color = SUNK
                elif v == "X":
                    color = BLOCKED
                elif max_score > 0:
                    t = (score[r][c] / max_score) ** 0.5
                    color = tuple(int(a + (b - a) * t) for a, b in zip(GRID_BG, HOT))

                pg.draw.rect(self.screen, color, rect)
                pg.draw.rect(self.screen, LINE, rect, 1)

                if v == " " and score[r][c] > 0:
                    pct = score[r][c] / total * 100
                    txt = f"{pct:.0f}" if pct >= 10 else f"{pct:.1f}"
                    img = self.num_font.render(txt, True, (20, 20, 20) if t > 0.6 else DIM)
                    self.screen.blit(img, img.get_rect(center=rect.center))

        # White outline on the cell the bot chose
        if move is not None:
            mr, mc = move
            pg.draw.rect(
                self.screen, (255, 255, 255),
                pg.Rect(mx + mc * cell, top + mr * cell, cell, cell), 3,
            )

        # Text panel
        y = top + SIZE * cell + 12
        lines = [status, "Ships left (sizes): " + (" ".join(map(str, remaining)) or "none")]
        best = sorted(unknown, key=lambda rc: score[rc[0]][rc[1]], reverse=True)[:3]
        if best and max_score > 0:
            lines.append(
                "Top: " + "   ".join(
                    f"{chr(ord('A') + c)}{r + 1} {score[r][c] / total * 100:.1f}%" for r, c in best
                )
            )
        for line in lines:
            self.screen.blit(self.font.render(line, True, TEXT), (mx, y))
            y += 22

        pg.display.flip()


def main():
    # ' ' unknown, 'M' miss, 'H' unresolved hit, 'S' hit belonging to a sunk ship, 'X' invalid/blocked
    board = [[" " for _ in range(SIZE)] for _ in range(SIZE)]
    remaining = dict(SHIPS)
    last_shot = None
    last_score = [[0.0] * SIZE for _ in range(SIZE)]
    last_mode = "WAITING"
    rng = random.Random()

    viewer = None
    # ENABLE_VIEWER is the main switch; the BOT_VIEW=0 env var can still force it off.
    if ENABLE_VIEWER and os.environ.get("BOT_VIEW", "1") != "0":
        try:
            viewer = Viewer(f"{BOT_NAME} - brain")
        except Exception:
            viewer = None  # no pygame / no display: just play without the window

    def refresh(status):
        if viewer is not None and viewer.alive:
            viewer.draw(board, last_score, last_shot, last_mode, list(remaining.values()), status)

    def fits(r, c, dr, dc, length):
        """Placement is legal if it stays on the board and touches no miss / sunk / blocked cell."""
        cells = []
        for i in range(length):
            rr, cc = r + dr * i, c + dc * i
            if not (0 <= rr < SIZE and 0 <= cc < SIZE):
                return None
            if board[rr][cc] in ("M", "S", "X"):
                return None
            cells.append((rr, cc))
        return cells

    def choose_move():
        score = [[0.0] * SIZE for _ in range(SIZE)]
        has_hits = any(board[r][c] == "H" for r in range(SIZE) for c in range(SIZE))

        for length in remaining.values():
            for r in range(SIZE):
                for c in range(SIZE):
                    for dr, dc in ((0, 1), (1, 0)):
                        cells = fits(r, c, dr, dc, length)
                        if cells is None:
                            continue
                        hit_count = sum(1 for (rr, cc) in cells if board[rr][cc] == "H")
                        if has_hits:
                            # Target mode: only placements explaining unresolved hits matter.
                            if hit_count == 0:
                                continue
                            weight = 100.0 ** hit_count
                        else:
                            weight = 1.0
                        for (rr, cc) in cells:
                            if board[rr][cc] == " ":
                                score[rr][cc] += weight

        best, best_cells = -1.0, []
        smallest = min(remaining.values()) if remaining else 2
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] != " ":
                    continue
                s = score[r][c]
                # Parity bonus in hunt mode: fewer cells needed to catch every ship.
                if not has_hits and smallest >= 2 and (r + c) % 2 == 0:
                    s *= 1.05
                if s > best + 1e-9:
                    best, best_cells = s, [(r, c)]
                elif abs(s - best) <= 1e-9:
                    best_cells.append((r, c))

        if best_cells:
            move = rng.choice(best_cells)
        else:
            # Fallback: any unknown cell.
            free = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == " "]
            move = rng.choice(free) if free else (0, 0)
        return move, score, has_hits

    def resolve_sunk(ship_name):
        length = SHIPS.get(ship_name)
        if last_shot is None:
            return
        lr, lc = last_shot
        board[lr][lc] = "H"
        if length is None:
            board[lr][lc] = "S"
            return
        # Find a straight line of unresolved hits of this length containing the last shot.
        for dr, dc in ((0, 1), (1, 0)):
            for offset in range(length):
                sr, sc = lr - dr * offset, lc - dc * offset
                cells = []
                ok = True
                for i in range(length):
                    rr, cc = sr + dr * i, sc + dc * i
                    if not (0 <= rr < SIZE and 0 <= cc < SIZE) or board[rr][cc] != "H":
                        ok = False
                        break
                    cells.append((rr, cc))
                if ok:
                    for (rr, cc) in cells:
                        board[rr][cc] = "S"
                    return
        board[lr][lc] = "S"

    refresh("Waiting for first turn...")

    for line in sys.stdin:
        msg = line.strip()

        if msg == "YOUR_TURN":
            (r, c), last_score, hunting_hits = choose_move()
            last_shot = (r, c)
            last_mode = "TARGET" if hunting_hits else "HUNT"
            coord = f"{chr(ord('A') + c)}{r + 1}"
            print(coord)
            sys.stdout.flush()
            refresh(f"Firing at {coord}...")

        elif msg.startswith("RESULT:"):
            parts = msg.split(":", 2)
            status = parts[1] if len(parts) > 1 else ""
            if last_shot is None:
                continue
            r, c = last_shot
            if status == "MISS":
                board[r][c] = "M"
            elif status == "HIT":
                board[r][c] = "H"
            elif status == "SUNK":
                name = parts[2] if len(parts) > 2 else ""
                resolve_sunk(name)
                remaining.pop(name, None)
            elif status == "ALREADY_SHOT":
                if board[r][c] == " ":
                    board[r][c] = "M"
            elif status == "INVALID":
                if board[r][c] == " ":
                    board[r][c] = "X"

            text = f"Last shot {chr(ord('A') + c)}{r + 1}: {status}"
            if status == "SUNK" and len(parts) > 2:
                text += f" ({parts[2]})"
            refresh(text)

        elif msg == "GAME_OVER":
            break


if __name__ == "__main__":
    main()