"""
Ship type catalog for Battleship.

Define all available ship types here.
Each entry maps a display name to a shape (list of [dr, dc] offsets
from the anchor cell [0, 0]).

Shape rules:
  - Cells are [dr, dc] offsets; anchor is implicitly [0, 0].
  - Shapes must be orthogonally 4-connected (no diagonal-only adjacency).
    The game validates this at startup via validate_shape() -- any shape
    that fails 4-connectivity will raise ValueError before the window opens.
  - Shapes are defined in their canonical (un-rotated) orientation.
    The engine computes all distinct 90-degree clockwise rotations automatically.
  - A 1-cell ship has exactly 1 rotation.
  - A symmetric shape (square, etc.) may have fewer than 4 distinct rotations.

To add a new ship type:
  1. Add an entry to SHIP_TYPES below with the desired name and shape.
  2. Reference the name in a fleet preset in config_game.py.

To add a new fleet preset:
  See config_game.py -- presets reference ship names defined here.
"""

SHIP_TYPES = {
    "Patrol Boat": [[0, 0], [0, 1]],
    "Destroyer":   [[0, 0], [0, 1], [0, 2]],
    "Submarine":   [[0, 0], [0, 1], [0, 2]],
    "Battleship":  [[0, 0], [0, 1], [0, 2], [0, 3]],
    # Carrier: 5-cell L-shape fitting in a 2x3 bounding box (bottom-right absent).
    #   X X X
    #   X X .
    "Carrier":     [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1]],
}
