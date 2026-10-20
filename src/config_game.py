"""
Game configuration for Battleship.
All gameplay-affecting parameters live here.

Hard limits on board parameters:
  GRID_ROWS_MAX <= 16, GRID_COLS_MAX <= 16:
    At default CELL_SIZE=38 a 16x16 grid is about 624px per panel; two
    panels plus padding and labels may exceed 1280px on small displays.
  Fleet cells must fit in the grid:
    sum(size*count for each ship type) <= GRID_ROWS * GRID_COLS // 2
    to leave enough open water for randomised placement. The "standard"
    preset occupies 17 cells, safely within any grid >= 6x6.
  NUM_SHIPS_MAX per preset is bounded only by the cell-count constraint
    above; no hard cap is imposed beyond that.

Structural constant: only 2 players are supported. NUM_PLAYERS=2 is
referenced wherever the code relies on exactly two players.
"""

# -- Number of players (structural constant; only 2 is supported) ---------------
NUM_PLAYERS = 2

# -- Grid dimensions -----------------------------------------------------------
GRID_ROWS_MIN     = 6
GRID_ROWS_MAX     = 16
GRID_ROWS_DEFAULT = 10

GRID_COLS_MIN     = 6
GRID_COLS_MAX     = 16
GRID_COLS_DEFAULT = 10

# -- Fleet presets --------------------------------------------------------------
# Each preset is a list of ship specifications.
# Each spec: {"name": str (must exist in config_ships.SHIP_TYPES), "count": int}
# Shapes are resolved from config_ships.SHIP_TYPES by expand_fleet_spec() at runtime.
FLEET_PRESETS = {
    "standard": [
        {"name": "Carrier",     "count": 1},
        {"name": "Battleship",  "count": 1},
        {"name": "Destroyer",   "count": 1},
        {"name": "Submarine",   "count": 1},
        {"name": "Patrol Boat", "count": 1},
    ],
    "mini": [
        {"name": "Destroyer",   "count": 1},
        {"name": "Patrol Boat", "count": 2},
    ],
    "large": [
        {"name": "Carrier",     "count": 2},
        {"name": "Battleship",  "count": 2},
        {"name": "Destroyer",   "count": 2},
        {"name": "Submarine",   "count": 1},
        {"name": "Patrol Boat", "count": 2},
    ],
}

FLEET_PRESET_NAMES   = tuple(FLEET_PRESETS.keys())
FLEET_PRESET_DEFAULT = "standard"

# -- AI engine -----------------------------------------------------------------
AI_ENGINE = "hunt_target"    # module name inside ai_engines/

# -- AI / turn timing ----------------------------------------------------------
AI_THINK_DELAY_MS       = 500   # pause before AI fires (shows "thinking" status)
AI_INTER_MOVE_PAUSE_MS  = 300   # pause after each committed shot before next phase
AI_PLACEMENT_DELAY_MS   = 80    # ms between consecutive AI ship placements (visual)
RESULT_HOLD_MS          = 700   # extra ms the hit/miss/sunk message stays before next turn

# -- Fleet-grid display --------------------------------------------------------
# When True, cells where the opponent fired and missed are marked on the fleet
# grid with a small symbol (see config_text.FLEET_MISS_MARK_TEXT).
SHOW_OPPONENT_MISSES    = True

# -- Hit/miss flash animation --------------------------------------------------
HIT_FLASH_COUNT        = 4     # on/off half-cycles for a hit cell flash
HIT_FLASH_INTERVAL_MS  = 120   # ms per half-cycle

MISS_FLASH_COUNT       = 2     # on/off half-cycles for a miss cell flash
MISS_FLASH_INTERVAL_MS = 150   # ms per half-cycle

# -- Sunk ship animation -------------------------------------------------------
SUNK_FLASH_COUNT        = 8    # extra flashes when a ship is sunk
SUNK_FLASH_INTERVAL_MS  = 100  # ms per half-cycle for sunk animation

# -- Game-over flash -----------------------------------------------------------
WIN_FLASH_COUNT        = 6
WIN_FLASH_INTERVAL_MS  = 150

# -- Autoplay (testing / demo) -------------------------------------------------
AUTOPLAY_MOVE_DELAY_MS       = 600   # delay before each autoplay shot
AUTOPLAY_PLACEMENT_DELAY_MS  = 50    # delay between autoplay ship placements
AUTOPLAY_HANDOFF_SPLASH_MS   = 1500  # how long the auto-dismiss placement splash stays

# -- Advantage score scale (used by compute_advantage_score in game_logic) -----
ADVANTAGE_SCALE = 1000

# -- Live stats panel (shown between or beside the two grids during attack phase) -
# "middle" places the panel between the fleet grid and the attack grid.
# "right"  places it to the right of the attack grid.
STATS_PANEL_POSITION = "middle"   # "middle" or "right"

# -- Start-screen defaults -----------------------------------------------------
DEFAULT_FIRST_PLAYER = "human"   # "human" = human attacks first; "ai" = AI attacks first
