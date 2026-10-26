import csv
import subprocess
import sys
from pathlib import Path
from engine.board import Board

def run_single_solo_game(bot_script_path):
  """Spawns your actual bot script as a subprocess and plays a solo game."""
  board = Board()
  board.place_fleet_randomly()

  # Launch the real bot script file as a subprocess
  proc = subprocess.Popen(
      [sys.executable, bot_script_path],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      text=True,
  )

  turns = 0
  max_turns = 200  # Safety limit
  won = False

  try:
    while turns < max_turns and not board.all_ships_sunk():
      turns += 1

      # Ask the real bot script for its turn via stdin
      proc.stdin.write("YOUR_TURN\n")
      proc.stdin.flush()
      
      result = "INVALID"

      # Read its coordinate response from stdout
      while result == "ALREADY_SHOT" or result == "INVALID":
            proc.stdin.write("YOUR_TURN\n")
            proc.stdin.flush()
            move_line = proc.stdout.readline().strip()

            # Process shot on opponent's board
            
            col = ord(move_line[0]) - ord("A")
            row = int(move_line[1:]) - 1
            result = board.receive_shot(row, col)

      # Process shot on the secret benchmark board
      board.receive_shot(row, col)

      if board.all_ships_sunk():
        won = True
        break

  finally:
    # Clean up the bot process
    proc.stdin.write("GAME_OVER\n")
    proc.stdin.flush()
    proc.terminate()
    proc.wait()

  return {"total_turns": turns, "win": won}


def run_benchmark(bot_script_path, num_games=100):
  bot_name = Path(bot_script_path).stem
  print(
      f"Benchmarking real script [{bot_script_path}] over {num_games}"
      " games..."
  )
  print(
      "   (Spawning subprocesses—this might take a couple of seconds for"
      " 100+ games)"
  )

  results_dir = Path("benchmarks")
  results_dir.mkdir(exist_ok=True)
  csv_file = results_dir / f"benchmark_{bot_name}.csv"

  total_turns_sum = 0
  wins_count = 0

  with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["game_id", "total_turns", "win"])

    for game_id in range(1, num_games + 1):
      result = run_single_solo_game(bot_script_path)

      total_turns_sum += result["total_turns"]
      if result["win"]:
        wins_count += 1

      writer.writerow(
          [game_id, result["total_turns"], "YES" if result["win"] else "NO"]
      )

  # Analytics
  avg_turns = total_turns_sum / num_games
  win_rate = (wins_count / num_games) * 100

  print("\n========================================")
  print(f"BENCHMARK RESULTS FOR: {bot_name}")
  print("========================================")
  print(f"Games Tested:       {num_games}")
  print(f"Win Rate:           {win_rate:.1f}%")
  print(f"Average Turns to Win: {avg_turns:.2f} turns")
  print(f"CSV Report Saved:   {csv_file}")
  print("========================================")


if __name__ == "__main__":
  target_bot = "bots/random_bot.py"
  
  # Run 100 games (you can increase this to 500 or 1000 once you make a smarter bot)
  run_benchmark(target_bot, num_games=1000)