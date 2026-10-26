import random
import sys


def main():
    # Letters for columns, numbers for rows
    columns = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    # Listen continuously to standard input from the referee
    for line in sys.stdin:
        message = line.strip()

        if message == "YOUR_TURN":
            # Generate a random shot coordinate
            col = random.choice(columns)
            row = random.randint(1, 10)
            move = f"{col}{row}"

            # Print the move to stdout so the referee can read it
            print(move)
            sys.stdout.flush()  # CRITICAL: Always flush stdout in bot scripts!

        elif message.startswith("GAME_OVER"):
            # Clean exit when the match finishes
            break


if __name__ == "__main__":
    main()
