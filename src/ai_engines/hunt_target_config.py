"""
Configuration for the Hunt-and-Target Battleship AI engine.

HUNT_MODE_CHECKERBOARD:
  In hunt mode, fire only at cells of one "colour" of the checkerboard
  pattern (cells where (row + col) % 2 == 0).  Since the smallest ship
  has size 2, every ship must span at least one cell of each parity, so
  the checkerboard filter halves the search space without missing any ship.
  Set to False to fire at all unknown cells instead.

PROBABILITY_DENSITY_ENABLED:
  In hunt mode, score each candidate cell by counting how many ways any
  remaining (unsunk) ship could be placed so as to pass through it.  The
  cell with the highest count is fired at first.  This is considerably
  stronger than random selection within the checkerboard.  Set to False
  to fall back to random selection within the checkerboard.

TARGET_ADJACENT_PRIORITY:
  In target mode (when there are active hit cells on an unsunk ship),
  prioritise cells that extend the known run direction over branching to
  new adjacent cells.  Eliminates wasted shots when multiple hits in a
  line have already revealed the ship's orientation.  Set to False to
  treat all adjacent unknown cells equally.
"""

HUNT_MODE_CHECKERBOARD      = True
PROBABILITY_DENSITY_ENABLED = True
TARGET_ADJACENT_PRIORITY    = True
