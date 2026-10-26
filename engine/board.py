import random


class Board:

    def __init__(self):
        self.size = 10
        # Grid state: ' ' = empty, 'S' = ship, 'H' = hit, 'M' = miss
        self.grid = [[" " for _ in range(self.size)] for _ in range(self.size)]

        # Track ships and their coordinates
        self.ships = {}

        # Standard Battleship fleet sizes
        self.ship_sizes = {
            "Carrier": 5,
            "Battleship": 4,
            "Destroyer": 3,
            "Submarine": 3,
            "PatrolBoat": 2,
        }

    def print_board(self, reveal_ships=False):
        """Helper method to print the board nicely in the console for debugging."""
        print("   A B C D E F G H I J")
        print("  --------------------")
        for r in range(self.size):
            row_str = f"{r+1:2}|"
            for c in range(self.size):
                cell = self.grid[r][c]
                if cell == "S" and not reveal_ships:
                    row_str += " ~|"  # Hide unhit ships if opponent is looking
                else:
                    row_str += f" {cell}|"
            print(row_str)
        print("  --------------------")

    def place_ship(self, ship_name, start_row, start_col, direction):
        """Places a ship on the board.

        direction: 'H' (Horizontal) or 'V' (Vertical)
        """
        if ship_name not in self.ship_sizes:
            raise ValueError(f"Unknown ship name: {ship_name}")

        length = self.ship_sizes[ship_name]
        coords = []

        # Calculate and validate coordinates
        for i in range(length):
            r = start_row + (i if direction == "V" else 0)
            c = start_col + (i if direction == "H" else 0)

            # Check boundary limits
            if not (0 <= r < self.size and 0 <= c < self.size):
                return False

            # Check for overlapping ships
            if self.grid[r][c] == "S":
                return False

            coords.append((r, c))

        # Place the ship
        for r, c in coords:
            self.grid[r][c] = "S"

        self.ships[ship_name] = {"coords": coords, "hits": 0}
        return True

    def receive_shot(self, coord):
        """Processes an incoming shot.

        Returns: 'MISS', 'HIT', 'SUNK:<ship_name>', 'ALREADY_SHOT', or 'INVALID'
        """
        col = ord(coord[0]) - ord("A")
        row = int(coord[1:]) - 1
        
        
        if not (0 <= row < self.size and 0 <= col < self.size):
            return "INVALID"

        current = self.grid[row][col]

        if current in ("H", "M"):
            return "ALREADY_SHOT"

        if current == " ":
            self.grid[row][col] = "M"
            return "MISS"

        if current == "S":
            self.grid[row][col] = "H"

            # Update ship hit counter and check if it sank
            for ship_name, data in self.ships.items():
                if (row, col) in data["coords"]:
                    data["hits"] += 1
                    if data["hits"] == len(data["coords"]):
                        return f"SUNK:{ship_name}"
                    return "HIT"

        return "INVALID"

    def all_ships_sunk(self):
        """Returns True if every ship on the board has been completely sunk."""
        if not self.ships:
            return False
        return all(data["hits"] == len(data["coords"]) for data in self.ships.values())

    def place_fleet_randomly(board):
        """Randomly places all standard ships onto a board."""
        for ship_name in board.ship_sizes.keys():
            placed = False
            while not placed:
                row = random.randint(0, 9)
                col = random.randint(0, 9)
                direction = random.choice(["H", "V"])
                placed = board.place_ship(ship_name, row, col, direction)
