import subprocess
import sys
import time
from engine.board import Board
import pygame


class BattleshipReferee:

    def __init__(self, bot_1_script_path, bot_2_script_path):
        self.bot_1_path = bot_1_script_path
        self.bot_2_path = bot_2_script_path
        self.bot1 = None
        self.bot2 = None
        self.board_bot_1 = Board()
        self.board_bot_1.place_fleet_randomly()
        self.board_bot_2 = Board()
        self.board_bot_2.place_fleet_randomly()

        # --- Pygame Setup ---
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 480
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Battleship Tournament - Initializing...")
        self.clock = pygame.time.Clock()
        self.DELAY_BTW_SHOTS = 100

        # Colors
        self.BG_COLOR = (30, 30, 35)
        self.GRID_BG = (45, 45, 52)
        self.LINE_COLOR = (70, 70, 80)
        self.CELL_SIZE = 35
        self.MARGIN_X = 50
        self.MARGIN_Y = 50

        # Piece Colors
        self.SHIP_COLOR = (100, 110, 130)  # Slate grey for ships
        self.HIT_COLOR = (220, 50, 50)  # Vibrant red for hits
        self.MISS_COLOR = (100, 180, 255)  # Soft blue for misses

    def start_bots(self):
        """Spawns the bot as a separate subprocess."""
        self.bot1 = subprocess.Popen(
            [sys.executable, self.bot_1_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.bot2 = subprocess.Popen(
            [sys.executable, self.bot_2_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )

    def play_turn(self, attacker_proc, defender_board, attacker_name):
        """Executes a single turn for a bot."""
        result = "INVALID"

        while result == "ALREADY_SHOT" or result == "INVALID":
            attacker_proc.stdin.write("YOUR_TURN\n")
            attacker_proc.stdin.flush()
            move_line = attacker_proc.stdout.readline().strip()

            # Process shot on opponent's board
            result = defender_board.receive_shot(move_line)

        print(f"[{attacker_name}] fires at {move_line} ➔ Result: {result}")
        return move_line, result

    def run_game(self):
        print("========================================")
        print(" BATTLESHIP TOURNAMENT: MATCH STARTING ")
        print("========================================")
        status = "Match Started. Bots are firing..."
        # Initial render
        self.render_frame(status)
        time.sleep(1)

        self.start_bots()

        turn_count = 0
        max_turns = 200  # Safety limit to prevent infinite loops
        winner = None

        try:
            while turn_count < max_turns:
                turn_count += 1

                # --- Player 1 Turn ---
                print(f"\n--- Turn {turn_count} ---")
                move1, res1 = self.play_turn(
                    self.bot1, self.board_bot_2, "Bot 1 (Player 1)"
                )
                status = f"Turn {turn_count}: Bot 1 fires at {move1} -> {res1}"
                self.render_frame(status)
                if self.board_bot_2.all_ships_sunk():
                    winner = "Bot 1 (Player 1)"
                    break

                # Small delay for readable console output
                pygame.time.delay(self.DELAY_BTW_SHOTS)

                # --- Player 2 Turn ---
                move2, res2 = self.play_turn(
                    self.bot2, self.board_bot_1, "Bot 2 (Player 2)"
                )
                status = f"Turn {turn_count}: Bot 2 fires at {move2} -> {res2}"
                self.render_frame(status)
                if self.board_bot_1.all_ships_sunk():
                    winner = "Bot 2 (Player 2)"
                    break

                pygame.time.delay(self.DELAY_BTW_SHOTS)

        finally:
            # Clean up bot processes
            if self.bot1:
                self.bot1.terminate()
            if self.bot2:
                self.bot2.terminate()

        print("\n========================================")
        if winner:
            print(f"GAME OVER! Winner: {winner} in {turn_count} turns!")
        else:
            print("GAME OVER! Match reached turn limit (Draw).")
        print("========================================")

    def draw_grid(self, start_x, start_y, board):
        """Draws a 10x10 grid on the Pygame window."""
        for r in range(10):
            for c in range(10):
                rect = pygame.Rect(
                    start_x + c * self.CELL_SIZE,
                    start_y + r * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )

                cell_value = board.grid[r][c]
                color = self.GRID_BG
                if cell_value == "S":
                    color = self.SHIP_COLOR
                elif cell_value == "H":
                    color = self.HIT_COLOR
                elif cell_value == "M":
                    color = self.MISS_COLOR

                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, self.LINE_COLOR, rect, 1)


    def render_frame(self, status_text=""):
        """Redraws the boards and updates the window title status."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        self.screen.fill(self.BG_COLOR)

        # Draw Player 1 Board (Left) & Player 2 Board (Right)
        self.draw_grid(self.MARGIN_X, self.MARGIN_Y, self.board_bot_1)
        self.draw_grid(self.MARGIN_X + 380, self.MARGIN_Y, self.board_bot_2)

        # Display game status in the top window title bar
        pygame.display.set_caption(f"Battleship Tournament | {status_text}")
        pygame.display.flip()


MATCH_COUNT = 1

if __name__ == "__main__":
    bot_script = "bots/random_bot.py"
    for match_number in range(1, MATCH_COUNT + 1):
        print(f"\n\n=== MATCH {match_number} ===")
        match = BattleshipReferee(bot_script, bot_script)
        match.run_game()
