"""Visualize a Battleship benchmark CSV.

Usage:
    python visualize_benchmark.py benchmarks/benchmark_claude.csv

Needs: pip install pandas matplotlib numpy
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SIZES = {"Carrier": 5, "Battleship": 4, "Destroyer": 3, "Submarine": 3, "PatrolBoat": 2}


def parse_placement(text):
    """'Carrier:A1H|Battleship:C3V|...' -> {ship: [(row, col), ...]}"""
    ships = {}
    for part in text.split("|"):
        name, spec = part.split(":")
        col = ord(spec[0]) - ord("A")
        row = int(spec[1:-1]) - 1
        direction = spec[-1]
        ships[name] = [
            (row + (i if direction == "V" else 0), col + (i if direction == "H" else 0))
            for i in range(SIZES[name])
        ]
    return ships


def main(csv_path):
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    placements = df["placement"].map(parse_placement)

    sums = np.zeros((10, 10))
    counts = np.zeros((10, 10))
    center_dist = []

    for turns, ships in zip(df["total_turns"], placements):
        cells = [rc for coords in ships.values() for rc in coords]
        for r, c in cells:
            sums[r, c] += turns
            counts[r, c] += 1
        center_dist.append(np.mean([np.hypot(r - 4.5, c - 4.5) for r, c in cells]))

    df["center_dist"] = center_dist
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_turns = sums / counts

    mean = df["total_turns"].mean()
    median = df["total_turns"].median()
    corr = df["total_turns"].corr(df["center_dist"])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Benchmark: {csv_path.stem}  ({len(df)} games)", fontsize=14)

    # 1. Distribution of turns
    ax = axes[0, 0]
    ax.hist(df["total_turns"], bins=range(0, int(df["total_turns"].max()) + 5, 2),
            color="#4c78a8", edgecolor="white")
    ax.axvline(mean, color="red", linestyle="--", label=f"mean {mean:.1f}")
    ax.axvline(median, color="orange", linestyle="--", label=f"median {median:.1f}")
    ax.set(title="Turns per game", xlabel="turns", ylabel="games")
    ax.legend()

    # 2. Running average (has the benchmark converged?)
    ax = axes[0, 1]
    ax.plot(df["game_id"], df["total_turns"].expanding().mean(), color="#54a24b")
    ax.set(title="Running average of turns", xlabel="games played", ylabel="avg turns")
    ax.grid(alpha=0.3)

    # 3. Heatmap: avg turns the bot needed when a ship covered each cell
    ax = axes[1, 0]
    im = ax.imshow(mean_turns, cmap="viridis", origin="upper")
    ax.set_xticks(range(10), list("ABCDEFGHIJ"))
    ax.set_yticks(range(10), range(1, 11))
    ax.set(title="Avg turns to win when a ship covers the cell\n(brighter = harder for the bot)")
    fig.colorbar(im, ax=ax, label="avg turns")

    # 4. Ship position vs turns
    ax = axes[1, 1]
    ax.scatter(df["center_dist"], df["total_turns"], alpha=0.25, s=12, color="#e45756")
    z = np.polyfit(df["center_dist"], df["total_turns"], 1)
    xs = np.linspace(df["center_dist"].min(), df["center_dist"].max(), 50)
    ax.plot(xs, np.polyval(z, xs), color="black")
    ax.set(title=f"Fleet distance from center vs turns (r = {corr:.2f})",
           xlabel="avg distance of ship cells from board center", ylabel="turns")

    fig.tight_layout()
    out = csv_path.with_suffix(".png")
    fig.savefig(out, dpi=150)
    print(f"Saved {out}")

    # Best / worst placements (for the defender, more turns = better)
    cols = ["game_id", "total_turns", "placement"]
    print("\nHardest placements for the bot (most turns):")
    print(df.nlargest(5, "total_turns")[cols].to_string(index=False))
    print("\nEasiest placements for the bot (fewest turns):")
    print(df.nsmallest(5, "total_turns")[cols].to_string(index=False))

    plt.show()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "benchmarks/benchmark_hunter.csv")