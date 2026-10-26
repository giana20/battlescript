import os
import subprocess
import sys
import time
from engine.board import Board
import pygame
from pathlib import Path


class BattleshipReferee:

    def __init__(self, bot_1_script_path, bot_2_script_path):
        self.bot_1_path = bot_1_script_path
        self.bot_2_path = bot_2_script_path
        self.bot1_name = Path(bot_1_script_path).stem
        self.bot2_name = Path(bot_2_script_path).stem
        self.bot1 = None
        self.bot2 = None
        self.board_bot_1 = Board()
        self.board_bot_1.place_fleet_randomly()
        self.board_bot_2 = Board()
        self.board_bot_2.place_fleet_randomly()

        # Where each bot's own "brain" window opens (x,y in screen pixels).
        # Tweak these for your monitor.
        self.BOT_WINDOW_POS = ("860,40", "1280,40")

        # --- Pygame Setup ---
        pygame.init()
        self.font = pygame.font.SysFont("arial", 24, bold=True)
        self.WIDTH, self.HEIGHT = 800, 480
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Battleship Tournament - Initializing...")
        self.clock = pygame.time.Clock()
        self.DELAY_BTW_SHOTS = 1000

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

    def _spawn(self, script_path, window_pos):
        """Spawns a bot as a separate subprocess."""
        env = os.environ.copy()
        env["BOT_WINDOW_POS"] = window_pos
        return subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=env,
        )

    def start_bots(self):
        self.bot1 = self._spawn(self.bot_1_path, self.BOT_WINDOW_POS[0])
        self.bot2 = self._spawn(self.bot_2_path, self.BOT_WINDOW_POS[1])

    def play_turn(self, attacker_proc, defender_board, attacker_name):
        """Executes a single turn for a bot."""
        result = "INVALID"

        while result == "ALREADY_SHOT" or result == "INVALID":
            attacker_proc.stdin.write("YOUR_TURN\n")
            attacker_proc.stdin.flush()
            move_line = attacker_proc.stdout.readline().strip()

            # Process shot on opponent's board
            col = ord(move_line[0]) - ord("A")
            row = int(move_line[1:]) - 1
            result = defender_board.receive_shot(row, col)

        print(f"[{attacker_name}] fires at {move_line} ➔ Result: {result}")
        attacker_proc.stdin.write(f"RESULT:{result}\n")
        attacker_proc.stdin.flush()
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
                    self.bot1, self.board_bot_2, self.bot1_name
                )
                status = f"Turn {turn_count}: Bot 1 fires at {move1} -> {res1}"
                self.render_frame(status)
                if self.board_bot_2.all_ships_sunk():
                    winner = self.bot1_name
                    break

                # Small delay for readable console output
                pygame.time.delay(self.DELAY_BTW_SHOTS)

                # --- Player 2 Turn ---
                move2, res2 = self.play_turn(
                    self.bot2, self.board_bot_1, self.bot2_name
                )
                status = f"Turn {turn_count}: Bot 2 fires at {move2} -> {res2}"
                self.render_frame(status)
                if self.board_bot_1.all_ships_sunk():
                    winner = self.bot2_name
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

    def draw_label(self, text, start_x, start_y):
        """Draws a centered label above a grid."""
        grid_width = 10 * self.CELL_SIZE
        label = self.font.render(text, True, (235, 235, 240))
        label_rect = label.get_rect(center=(start_x + grid_width // 2, start_y - 20))
        self.screen.blit(label, label_rect)

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

        self.draw_label(self.bot1_name, self.MARGIN_X, self.MARGIN_Y)
        self.draw_label(self.bot2_name, self.MARGIN_X + 380, self.MARGIN_Y)

        # Display game status in the top window title bar
        pygame.display.set_caption(f"Battleship Tournament | {status_text}")
        pygame.display.flip()


MATCH_COUNT = 1

if __name__ == "__main__":
    bot_1_script = "bots/chatgpt.py"
    bot_2_script = "bots/claude.py"
    for match_number in range(1, MATCH_COUNT + 1):
        print(f"\n\n=== MATCH {match_number} ===")
        match = BattleshipReferee(bot_1_script, bot_2_script)
        match.run_game()