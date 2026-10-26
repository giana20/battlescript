import random
import sys


def main():
  # Local view of the board: ' ' = unknown, 'M' = miss, 'H' = hit
  board_state = [[" " for _ in range(10)] for _ in range(10)]

  # Stack of high-priority targets when a ship is hit
  target_stack = []

  # Parity (checkerboard) hunting coordinates to optimize finding ships
  parity_shots = [(r, c) for r in range(10) for c in range(10) if (r + c) % 2 == 0]
  random.shuffle(parity_shots)

  fallback_shots = [
      (r, c) for r in range(10) for c in range(10) if (r + c) % 2 != 0
  ]
  random.shuffle(fallback_shots)

  last_shot = None

  for line in sys.stdin:
    msg = line.strip()

    if msg == "YOUR_TURN":
      shot = None

      # Priority 1: Target adjacent cells from previous hits
      while target_stack:
        r, c = target_stack.pop()
        if board_state[r][c] == " ":
          shot = (r, c)
          break

      # Priority 2: Parity hunting shots
      if not shot and parity_shots:
        r, c = parity_shots.pop()
        if board_state[r][c] == " ":
          shot = (r, c)

      # Priority 3: Fallback random shots
      if not shot and fallback_shots:
        r, c = fallback_shots.pop()
        if board_state[r][c] == " ":
          shot = (r, c)

      # Final fallback
      if not shot:
        for r in range(10):
          for c in range(10):
            if board_state[r][c] == " ":
              shot = (r, c)
              break
          if shot:
            break

      last_shot = shot
      col_char = chr(ord("A") + shot[1])
      row_num = shot[0] + 1
      move = f"{col_char}{row_num}"

      print(move)
      sys.stdout.flush()

    elif msg.startswith("RESULT:"):
      # Receive feedback from referee e.g., "RESULT:HIT" or "RESULT:SUNK:Carrier"
      result_type = msg.split(":")[1]

      if last_shot:
        r, c = last_shot
        if result_type == "MISS":
          board_state[r][c] = "M"
        elif result_type == "HIT":
          board_state[r][c] = "H"
          # Add orthogonal neighbors (North, South, East, West) to target queue
          for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board_state[nr][nc] == " ":
              target_stack.append((nr, nc))
        elif result_type.startswith("SUNK"):
          board_state[r][c] = "H"
          # Ship sunk! Clear targets to resume hunting for remaining ships
          target_stack.clear()

    elif msg == "GAME_OVER":
      break


if __name__ == "__main__":
  main()