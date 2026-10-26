import sys
from collections import deque

def main():
    # Initialize your bot's internal tracking state or board
    # ' ' = unknown, 'M' = miss, 'H' = hit, 'S' = sunk
    board = [[" " for _ in range(10)] for _ in range(10)]
    
    # Track unsunk hits to guide the targeting phase
    hits = []
    
    # Queue for specific cells to shoot next (adjacent to hits)
    targets = deque()
    targets_set = set()
    
    last_shot = None

    for line in sys.stdin:
        msg = line.strip()
        if not msg:
            continue

        if msg == "YOUR_TURN":
            target_row, target_col = -1, -1
            found_target = False

            # --- PHASE 1: TARGETING ---
            # If we have hits on unsunk ships, shoot adjacent cells
            while targets:
                t = targets.popleft()
                targets_set.discard(t)
                tr, tc = t
                # Ensure we don't shoot a cell that is already known
                if board[tr][tc] == " ":
                    target_row, target_col = tr, tc
                    found_target = True
                    break

            # --- PHASE 2: HUNTING (Checkerboard Parity) ---
            # If no specific targets, hunt using a checkerboard pattern.
            # Since the smallest ship is 2 cells, a parity of 2 guarantees 
            # we will eventually hit every ship while minimizing wasted shots.
            if not found_target:
                for r in range(10):
                    for c in range(10):
                        if board[r][c] == " " and (r + c) % 2 == 0:
                            target_row, target_col = r, c
                            found_target = True
                            break
                    if found_target:
                        break

            # --- PHASE 3: FALLBACK ---
            # If all parity cells are exhausted, shoot any remaining unknown cell
            if not found_target:
                for r in range(10):
                    for c in range(10):
                        if board[r][c] == " ":
                            target_row, target_col = r, c
                            found_target = True
                            break
                    if found_target:
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
            # Parse feedback from referee
            parts = msg.split(":")
            result_type = parts[1]
            
            if last_shot:
                r, c = last_shot
                
                if result_type == "MISS":
                    board[r][c] = "M"
                    
                elif result_type == "HIT":
                    board[r][c] = "H"
                    hits.append((r, c))
                    
                    # Add valid adjacent cells to our targeting queue
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 10 and 0 <= nc < 10:
                            if board[nr][nc] == " " and (nr, nc) not in targets_set:
                                targets.append((nr, nc))
                                targets_set.add((nr, nc))
                                
                elif result_type == "SUNK":
                    # The last shot sunk a ship. We temporarily mark it as 'H' 
                    # to allow flood-fill to find all connected segments of this ship.
                    board[r][c] = "H"
                    
                    sunk_cells = []
                    stack = [(r, c)]
                    visited = set()
                    
                    # Flood fill to find all parts of the newly sunk ship
                    while stack:
                        curr = stack.pop()
                        if curr in visited:
                            continue
                        visited.add(curr)
                        cr, cc = curr
                        
                        if board[cr][cc] == "H":
                            sunk_cells.append(curr)
                            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                nr, nc = cr + dr, cc + dc
                                if 0 <= nr < 10 and 0 <= nc < 10:
                                    if (nr, nc) not in visited:
                                        stack.append((nr, nc))
                    
                    # Mark all segments of the sunk ship as 'S' and remove from hits list
                    for sr, sc in sunk_cells:
                        board[sr][sc] = "S"
                        if (sr, sc) in hits:
                            hits.remove((sr, sc))
                            
                    # Rebuild the targeting queue based on any remaining unsunk hits
                    targets.clear()
                    targets_set.clear()
                    for hr, hc in hits:
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = hr + dr, hc + dc
                            if 0 <= nr < 10 and 0 <= nc < 10:
                                if board[nr][nc] == " " and (nr, nc) not in targets_set:
                                    targets.append((nr, nc))
                                    targets_set.add((nr, nc))
                                    
                elif result_type in ("ALREADY_SHOT", "INVALID"):
                    # Ignore invalid states, board remains unchanged
                    pass

        elif msg == "GAME_OVER":
            break

if __name__ == "__main__":
    main()