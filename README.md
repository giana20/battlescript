# Project Specification: Cross-Platform Battleship Bot Tournament & Benchmark System

## 1. Project Overview

This project is a cross-platform (Linux & Windows) competitive framework for AI bots playing the game of **Battleship**.
To ensure maximum flexibility, bots can be written in any language, but the core tournament runner, game engine, and match referee are built in **Python**. Isolation between the game engine (Referee) and the competing bots is achieved using **Standard Input/Output (`stdin`/`stdout`) process piping**, preventing bots from crashing the game or cheating by inspecting memory.

---

## 2. Directory Structure

```text
battleship_tournament/
├── bots/                  # Folder containing all competitor bot scripts
│   ├── random_bot.py      # Baseline random shooter
│   └── hunter_bot.py      # Parity + Target-mode smart bot
├── engine/                # Core game rules and board logic
│   ├── __init__.py        # Package initializer
│   └── board.py           # 10x10 Grid, ship placement, hit/miss/sunk logic
├── benchmarks/            # CSV outputs for solo performance testing
├── match_logs/            # JSON match records (optional for replays)
├── main.py                # Visual match referee (Pygame live window)
└── benchmark.py           # Solo efficiency testing script (CSV generation)

```

---

## 3. The Communication Protocol (IPC)

The Referee and the Bots communicate via **Standard Input (`stdin`)** and **Standard Output (`stdout`)**.

### Referee $\rightarrow$ Bot Messages (Sent to Bot's `stdin`):

* `YOUR_TURN\n` — Tells the bot it is its turn to fire.
* `RESULT:<STATUS>\n` — Gives feedback on the bot's last shot. `<STATUS>` can be:
* `MISS`
* `HIT`
* `SUNK:<ShipName>` (e.g., `SUNK:Carrier`)
* `INVALID`


* `GAME_OVER\n` — Signals that the match has concluded.

### Bot $\rightarrow$ Referee Messages (Printed to Bot's `stdout`):

* A coordinate string representing the target, e.g., `C4`, `A1`, `H10`. *(Must be immediately followed by `sys.stdout.flush()`)*.

---

## 4. Game Rules & Board Specification

* **Grid Size:** $10 \times 10$ grid. Columns are labeled **A through J** (left to right), and rows are numbered **1 through 10** (top to bottom).
* **Fleet Configuration:** Each player starts with 5 standard ships:
* **Carrier:** Length 5
* **Battleship:** Length 4
* **Destroyer:** Length 3
* **Submarine:** Length 3
* **PatrolBoat:** Length 2


* **Win Condition:** The first bot to completely sink all opponent ship segments wins the match.

---

## 5. Core Component Specifications

### A. Board Engine (`engine/board.py`)

Manages the grid state:

* Cell states: `' '` (Empty), `'S'` (Ship), `'H'` (Hit), `'M'` (Miss).
* Methods:
* `place_ship(ship_name, start_row, start_col, direction)` where direction is `'H'` or `'V'`.
* `receive_shot(row, col)` evaluates the shot and returns `'MISS'`, `'HIT'`, `'SUNK:<Name>'`, `'ALREADY_SHOT'`, or `'INVALID'`.
* `all_ships_sunk()` returns a boolean indicating match completion.



### B. Visual Match Referee (`main.py`)

* Spawns two bot subprocesses using `subprocess.Popen` with `sys.executable` (ensuring cross-platform Windows/Linux compatibility).
* Opens a **Pygame** graphical window displaying both player boards side-by-side.
* Alternates turns, sends prompts, receives coordinates, updates boards, and logs turn statuses into the window's title bar.

### C. Solo Benchmark (`benchmark.py`)

* Runs a single bot script file solo against thousands of randomly generated boards to test its efficiency.
* Bypasses UI overhead to simulate games instantly, logging performance metrics (`game_id`, `total_turns`, `win`) into a CSV file inside `benchmarks/`.

---

## 6. Template: How to Write a New Custom Bot

If you want to write a new bot script and drop it into the `bots/` folder, follow this standard template:

```python
import sys


def main():
  # Initialize your bot's internal tracking board or state here
  known_board = [[" " for _ in range(10)] for _ in range(10)]
  last_shot = None

  # Listen continuously to the referee via standard input
  for line in sys.stdin:
    msg = line.strip()

    if msg == "YOUR_TURN":
      # --- YOUR STRATEGY LOGIC HERE ---
      # Example: Pick the first available open space
      shot_row, shot_col = 0, 0
      for r in range(10):
        for c in range(10):
          if known_board[r][c] == " ":
            shot_row, shot_col = r, c
            break
        if known_board[shot_row][shot_col] != " ":
          break

      last_shot = (shot_row, shot_col)

      # Convert indices to Battleship notation (e.g., row 3, col 2 -> 'C4')
      col_char = chr(ord("A") + shot_col)
      row_num = shot_row + 1
      move = f"{col_char}{row_num}"

      # Output the move to stdout (CRITICAL: always flush!)
      print(move)
      sys.stdout.flush()

    elif msg.startswith("RESULT:"):
      # Learn from the outcome of your last shot
      result_type = msg.split(":")[1]
      if last_shot:
        r, c = last_shot
        if result_type == "MISS":
          known_board[r][c] = "M"
        elif result_type in ("HIT", "SUNK"):
          known_board[r][c] = "H"

    elif msg == "GAME_OVER":
      break


if __name__ == "__main__":
  main()

```

---

## 7. How to Execute the Scripts

* **Run a Live Visual Match:**
```bash
python3 main.py

```


* **Run Solo Benchmarks:**
```bash
python3 benchmark.py

```