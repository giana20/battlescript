import sys


def main():
    # Initialize your bot's internal tracking state or board
    # ' ' = unknown, 'M' = miss, 'H' = hit
    known_board = [[" " for _ in range(10)] for _ in range(10)]
    last_shot = None
    targets = []  # Queue/stack of coordinates to target after a HIT
    active_hits = []  # Hits belonging to the current ship being hunted

    for line in sys.stdin:
        msg = line.strip()

        if msg == "YOUR_TURN":
            target_row, target_col = None, None

            # 1. Target Mode: If we have pending target coordinates from a HIT, use them first
            while targets:
                r, c = targets.pop(0)
                if known_board[r][c] == " ":
                    target_row, target_col = r, c
                    break

            # 2. Hunt Mode: If no targets are active, use a Checkerboard (Parity) pattern
            if target_row is None:
                for parity in [0, 1]:
                    if target_row is not None:
                        break
                    for r in range(10):
                        for c in range(10):
                            if (
                                known_board[r][c] == " "
                                and (r + c) % 2 == parity
                            ):
                                target_row, target_col = r, c
                                break
                        if target_row is not None:
                            break

            # Fallback: If checkerboard spaces are exhausted, pick any open cell
            if target_row is None:
                for r in range(10):
                    for c in range(10):
                        if known_board[r][c] == " ":
                            target_row, target_col = r, c
                            break
                    if target_row is not None:
                        break

            last_shot = (target_row, target_col)

            # Convert to Battleship notation (e.g., row 3, col 2 -> 'C4')
            col_char = chr(ord("A") + target_col)
            row_num = target_row + 1
            move = f"{col_char}{row_num}"

            # Output move to referee (CRITICAL: always flush stdout)
            print(move)
            sys.stdout.flush()

        elif msg.startswith("RESULT:"):
            # Parse feedback from referee: "RESULT:HIT", "RESULT:MISS", "RESULT:SUNK:Carrier", etc.
            result_type = msg.split(":")[1]
            if last_shot:
                r, c = last_shot
                if result_type == "MISS":
                    known_board[r][c] = "M"
                elif result_type == "HIT":
                    known_board[r][c] = "H"
                    active_hits.append((r, c))
                    # Add valid orthogonal neighbors (up, down, left, right) to targets
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if (
                            0 <= nr < 10
                            and 0 <= nc < 10
                            and known_board[nr][nc] == " "
                        ):
                            if (nr, nc) not in targets:
                                targets.append((nr, nc))
                elif result_type.startswith("SUNK"):
                    known_board[r][c] = "H"
                    active_hits.append((r, c))
                    # Ship sunk! Clear targets for this ship and reset active hunt state
                    targets.clear()
                    active_hits.clear()
                elif result_type in ("ALREADY_SHOT", "INVALID"):
                    # Fallback safety in case of unexpected referee states
                    pass

        elif msg == "GAME_OVER":
            break


if __name__ == "__main__":
    main()