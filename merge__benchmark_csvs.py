import csv
from pathlib import Path


def merge_benchmark_csvs(output_filename="all_bot_benchmarks.csv"):
  results_dir = Path("benchmarks")
  output_path = results_dir / output_filename

  # Find all individual benchmark CSVs (excluding the combined one if it already exists)
  csv_files = [
      f for f in results_dir.glob("benchmark_*.csv") if f.name != output_filename
  ]

  if not csv_files:
    print("No benchmark CSV files found to merge in the 'benchmarks/' folder.")
    return

  print(f"Found {len(csv_files)} CSV files to merge...")

  with open(output_path, mode="w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    # Write updated header including the bot_name column
    writer.writerow(["bot_name", "game_id", "total_turns", "win", "placement"])

    for csv_file in csv_files:
      # Extract bot name from filename (e.g., "benchmark_chatgpt.csv" -> "chatgpt")
      bot_name = csv_file.stem.replace("benchmark_", "")

      with open(csv_file, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        next(reader)  # Skip the original header row

        for row in reader:
          # Prepend the bot_name to the row data and write to the master file
          writer.writerow([bot_name] + row)

  print(f"\nSuccessfully combined all files into:\n➡️  {output_path}")


if __name__ == "__main__":
  merge_benchmark_csvs()