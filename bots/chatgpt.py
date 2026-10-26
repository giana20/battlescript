
import sys
import random

SIZE = 10

SHIP_LENGTHS = {
    "Carrier": 5,
    "Battleship": 4,
    "Destroyer": 3,
    "Submarine": 3,
    "PatrolBoat": 2,
}

def main():
    # Board values: " " unknown, "M" miss, "H" hit.
    known_board = [[" " for _ in range(SIZE)] for _ in range(SIZE)]
    last_shot = None

    remaining_ships = SHIP_LENGTHS.copy()
    rng = random.Random()

    # All hits not yet accounted for by a sunk ship.
    active_hits = set()

    def in_bounds(r, c):
        return 0 <= r < SIZE and 0 <= c < SIZE

    def neighbors(r, c):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                yield nr, nc

    def target_candidates():
        """Return unknown cells adjacent to active hits."""
        candidates = set()

        for r, c in active_hits:
            for nr, nc in neighbors(r, c):
                if known_board[nr][nc] == " ":
                    candidates.add((nr, nc))

        # If hits establish a line, favor extending that line.
        for r, c in active_hits:
            horizontal = [
                (rr, cc) for rr, cc in active_hits if rr == r
            ]
            vertical = [
                (rr, cc) for rr, cc in active_hits if cc == c
            ]

            if len(horizontal) >= 2:
                lo = min(cc for _, cc in horizontal)
                hi = max(cc for _, cc in horizontal)
                candidates.discard((r, c))
                for cc in (lo - 1, hi + 1):
                    if in_bounds(r, cc) and known_board[r][cc] == " ":
                        candidates.add((r, cc))

            if len(vertical) >= 2:
                lo = min(rr for rr, _ in vertical)
                hi = max(rr for rr, _ in vertical)
                for rr in (lo - 1, hi + 1):
                    if in_bounds(rr, c) and known_board[rr][c] == " ":
                        candidates.add((rr, c))

        return candidates

    def probability_scores():
        """Count legal placements for each remaining ship."""
        scores = [[0] * SIZE for _ in range(SIZE)]

        for length in remaining_ships.values():
            for r in range(SIZE):
                for c in range(SIZE):
                    # Horizontal placement.
                    if c + length <= SIZE:
                        cells = [(r, cc) for cc in range(c, c + length)]
                        if all(known_board[rr][cc] == " " or
                               known_board[rr][cc] == "H"
                               for rr, cc in cells):
                            for rr, cc in cells:
                                if known_board[rr][cc] == " ":
                                    scores[rr][cc] += 1

                    # Vertical placement.
                    if r + length <= SIZE:
                        cells = [(rr, c) for rr in range(r, r + length)]
                        if all(known_board[rr][cc] == " " or
                               known_board[rr][cc] == "H"
                               for rr, cc in cells):
                            for rr, cc in cells:
                                if known_board[rr][cc] == " ":
                                    scores[rr][cc] += 1

        return scores

    def choose_shot():
        candidates = target_candidates()

        if candidates:
            # Probability-weighted target selection.
            scores = probability_scores()
            best_score = max(scores[r][c] for r, c in candidates)
            best = [
                (r, c) for r, c in candidates
                if scores[r][c] == best_score
            ]
            return rng.choice(best)

        scores = probability_scores()

        # Checkerboard hunt: all ships of length >= 2
        # must occupy at least one cell of this pattern.
        hunt = [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if known_board[r][c] == " " and (r + c) % 2 == 0
        ]

        # Prefer high-probability cells within the hunt pattern.
        if hunt:
            best_score = max(scores[r][c] for r, c in hunt)
            best = [
                (r, c) for r, c in hunt
                if scores[r][c] == best_score
            ]
            return rng.choice(best)

        # Fallback when no checkerboard cells remain.
        unknown = [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if known_board[r][c] == " "
        ]

        if not unknown:
            return None

        best_score = max(scores[r][c] for r, c in unknown)
        best = [
            (r, c) for r, c in unknown
            if scores[r][c] == best_score
        ]
        return rng.choice(best)

    for line in sys.stdin:
        msg = line.strip()

        if msg == "YOUR_TURN":
            last_shot = choose_shot()

            if last_shot is None:
                # Normally unreachable unless the board is exhausted.
                print("A1")
            else:
                r, c = last_shot
                print(f"{chr(ord('A') + c)}{r + 1}")

            sys.stdout.flush()

        elif msg.startswith("RESULT:"):
            result = msg[len("RESULT:"):]

            if last_shot is None:
                continue

            r, c = last_shot

            if result == "MISS":
                known_board[r][c] = "M"

            elif result == "HIT":
                known_board[r][c] = "H"
                active_hits.add((r, c))

            elif result.startswith("SUNK:"):
                known_board[r][c] = "H"
                active_hits.add((r, c))

                ship_name = result.split(":", 1)[1]
                ship_length = remaining_ships.pop(ship_name, None)

                # The sunk ship's hits are removed from active targeting.
                # Without per-ship hit labels, remove the connected
                # hit component containing the latest shot.
                component = set()
                stack = [(r, c)]

                while stack:
                    cell = stack.pop()
                    if cell in component or cell not in active_hits:
                        continue

                    component.add(cell)
                    cr, cc = cell

                    for nr, nc in neighbors(cr, cc):
                        if (nr, nc) in active_hits:
                            stack.append((nr, nc))

                active_hits.difference_update(component)

            elif result in ("ALREADY_SHOT", "INVALID"):
                # Do not mark a rejected shot as a hit or miss.
                # Avoid retrying it on the next turn.
                known_board[r][c] = "M"

            last_shot = None

        elif msg == "GAME_OVER":
            break


if __name__ == "__main__":
    main()
