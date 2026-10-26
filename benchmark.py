import csv
import random
from pathlib import Path
from engine.board import Board


class RandomBotSimulator:
  """A pure Python implementation of the Random Bot for fast solo simulation."""

  def __init__(self):
    self.reset()

  def reset(self):
    # Keep track of all available coordinates (0-9, 0-9) so it never repeats a shot
    self.available_shots = [(r, c) for r in range(10) for c in range(10)]
    random.shuffle(self.available_shots)

  def get_next_move(self):
    """Pops a random unshot coordinate."""
    if not self.available_shots:
      return None
    return self.available_shots.pop()


def run_single_game():
  """Simulates one complete solo game until all ships are sunk."""
  board = Board()
  board.place_fleet_randomly()

  bot = RandomBotSimulator()
  turns = 0
  max_turns = 100  # Safety limit

  while turns < max_turns and not board.all_ships_sunk():
    move = bot.get_next_move()
    if not move:
      break

    r, c = move
    board.receive_shot(r, c)
    turns += 1

  won = board.all_ships_sunk()
  return {
      "total_turns": turns,
      "win": won,
  }


def run_benchmark(num_games=1000):
  bot_name = "RandomBot"
  print(f"Starting solo benchmark: {num_games} games for [{bot_name}]...")

  # Ensure benchmarks directory exists
  results_dir = Path("benchmarks")
  results_dir.mkdir(exist_ok=True)
  csv_file = results_dir / f"benchmark_{bot_name.lower()}.csv"

  total_turns_sum = 0
  wins_count = 0

  # Open CSV file to save summary metrics
  with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Write CSV Header
    writer.writerow(["game_id", "total_turns", "win"])

    for game_id in range(1, num_games + 1):
      result = run_single_game()

      total_turns_sum += result["total_turns"]
      if result["win"]:
        wins_count += 1

      # Write row for this game
      writer.writerow(
          [game_id, result["total_turns"], "YES" if result["win"] else "NO"]
      )

  # Calculate final analytics
  avg_turns = total_turns_sum / num_games
  win_rate = (wins_count / num_games) * 100

  print("\n========================================")
  print(f"BENCHMARK RESULTS FOR: {bot_name}")
  print("========================================")
  print(f"Total Games Played: {num_games}")
  print(f"Win Rate:           {win_rate:.1f}%")
  print(f"Average Turns to Win: {avg_turns:.2f} turns")
  print(f"Results saved to:   {csv_file}")
  print("========================================")


if __name__ == "__main__":
  # Run 1,000 solo games instantly
  run_benchmark(num_games=1000)