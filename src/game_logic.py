"""
Core Battleship game logic. No UI imports.

Two-phase game:
  Phase 1 -- Ship placement (P1 first, then P2).
  Phase 2 -- Attack turns (alternating).

Board representations:
  fleet_board[row][col]  -- 0 = water, positive int = ship_id
  attack_board[row][col] -- 0 = unknown, 1 = miss, 2 = hit

Players: PLAYER_1 = 1, PLAYER_2 = 2

Phases:
  PHASE_P1_PLACEMENT  -- Player 1 is placing ships
  PHASE_P2_PLACEMENT  -- Player 2 is placing ships
  PHASE_P1_ATTACK     -- Player 1 fires at Player 2
  PHASE_P2_ATTACK     -- Player 2 fires at Player 1
  PHASE_DONE          -- game over
"""

import logging
from config_game import (
    GRID_ROWS_DEFAULT,
    GRID_COLS_DEFAULT,
    FLEET_PRESET_DEFAULT,
    FLEET_PRESETS,
    ADVANTAGE_SCALE,
    NUM_PLAYERS,
)

logger = logging.getLogger(__name__)

# -- Cell value constants -------------------------------------------------------
WATER     = 0   # fleet_board: empty water
UNKNOWN   = 0   # attack_board: not yet fired at
MISS_MARK = 1   # attack_board: shot that missed
HIT_MARK  = 2   # attack_board: shot that hit a ship

# -- Player constants -----------------------------------------------------------
PLAYER_1 = 1
PLAYER_2 = 2
OTHER_PLAYER = {PLAYER_1: PLAYER_2, PLAYER_2: PLAYER_1}

# -- Orientation constants ------------------------------------------------------
HORIZONTAL = True
VERTICAL   = False

# -- Phase constants ------------------------------------------------------------
PHASE_P1_PLACEMENT = "p1_placement"
PHASE_P2_PLACEMENT = "p2_placement"
PHASE_P1_ATTACK    = "p1_attack"
PHASE_P2_ATTACK    = "p2_attack"
PHASE_DONE         = "done"

PLACEMENT_PHASES = (PHASE_P1_PLACEMENT, PHASE_P2_PLACEMENT)
ATTACK_PHASES    = (PHASE_P1_ATTACK, PHASE_P2_ATTACK)


# -- Board helpers -------------------------------------------------------------

def make_fleet_board(num_rows, num_cols):
    """Return a 2-D list initialised to WATER."""
    return [[WATER] * num_cols for _ in range(num_rows)]


def make_attack_board(num_rows, num_cols):
    """Return a 2-D list initialised to UNKNOWN."""
    return [[UNKNOWN] * num_cols for _ in range(num_rows)]


def validate_shape(shape):
    """
    Raise ValueError if shape is not orthogonally 4-connected.
    Single-cell shapes are trivially valid.
    """
    cells = set(tuple(p) for p in shape)
    if len(cells) <= 1:
        return
    start = next(iter(cells))
    visited = {start}
    queue = [start]
    while queue:
        r, c = queue.pop()
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = (r + dr, c + dc)
            if nb in cells and nb not in visited:
                visited.add(nb)
                queue.append(nb)
    if visited != cells:
        raise ValueError("Shape is not orthogonally connected: " + str(shape))


def normalize_shape(shape):
    """Shift shape so min_row=0, min_col=0, then sort."""
    min_r = min(r for r, c in shape)
    min_c = min(c for r, c in shape)
    normalized = sorted((r - min_r, c - min_c) for r, c in shape)
    return [list(p) for p in normalized]


def rotate_shape_cw(shape):
    """Rotate shape 90 degrees clockwise: (dr, dc) -> (dc, -dr), then normalize."""
    rotated = [(c, -r) for r, c in shape]
    return normalize_shape(rotated)


def get_all_rotations(shape):
    """
    Return list of 1-4 distinct normalized rotations of shape.
    Validates that shape is orthogonally connected before computing rotations.
    """
    validate_shape(shape)
    rotations = []
    seen = set()
    current = normalize_shape(shape)
    for _ in range(4):
        key = tuple(tuple(p) for p in current)
        if key not in seen:
            seen.add(key)
            rotations.append(current)
        current = rotate_shape_cw(current)
    return rotations


def ship_cells(row, col, shape, num_rows, num_cols):
    """
    Return the list of (row, col) tuples for a ship with the given shape
    anchored at (row, col), or None if any cell is out of bounds.
    """
    cells = []
    for dr, dc in shape:
        r, c = row + dr, col + dc
        if r < 0 or r >= num_rows or c < 0 or c >= num_cols:
            return None
        cells.append((r, c))
    return cells


def can_place_ship(fleet_board, cells, num_rows, num_cols):
    """Return True if all cells are in-bounds and currently empty (WATER)."""
    if cells is None:
        return False
    for r, c in cells:
        if r < 0 or r >= num_rows or c < 0 or c >= num_cols:
            return False
        if fleet_board[r][c] != WATER:
            return False
    return True


def _write_ship_to_board(fleet_board, ship):
    """Write ship.ship_id into fleet_board at every cell the ship occupies."""
    for r, c in ship.cells:
        fleet_board[r][c] = ship.ship_id


def expand_fleet_spec(fleet_spec):
    """
    Convert a fleet_spec list of {name, count} dicts into a flat list
    of {name, shape} dicts, one entry per ship instance.
    Shapes are resolved from config_ships.SHIP_TYPES by name.
    Raises ValueError at startup if a name is not found in SHIP_TYPES.
    """
    from config_ships import SHIP_TYPES
    result = []
    for spec in fleet_spec:
        name = spec["name"]
        if name not in SHIP_TYPES:
            raise ValueError("Unknown ship type in fleet preset: " + repr(name))
        shape = SHIP_TYPES[name]
        for _ in range(spec["count"]):
            result.append({"name": name, "shape": shape})
    return result


# -- Ship class ----------------------------------------------------------------

class PlacedShip:
    """A ship instance that has been placed on a fleet board."""

    def __init__(self, ship_id, name, shape, cells, horizontal=None):
        self.ship_id = ship_id       # unique int >= 1 within a game
        self.name    = name          # display name
        self.shape   = shape         # rotated shape used for this placement
        self.size    = len(cells)    # number of cells (derived from shape)
        self.cells   = list(cells)   # list of (row, col) tuples
        self.hits    = set()         # set of (row, col) that have been hit

    @property
    def is_sunk(self):
        """True when every cell has been hit."""
        return len(self.hits) >= len(self.cells)

    def receive_hit(self, row, col):
        """Record a hit on the given cell."""
        self.hits.add((row, col))


# -- Attack result -------------------------------------------------------------

class AttackResult:
    """Encapsulates the outcome of a single attack."""

    def __init__(self, row, col, hit, sunk_ship=None):
        self.row       = row
        self.col       = col
        self.hit       = hit            # bool
        self.sunk_ship = sunk_ship      # PlacedShip | None


# -- Game state ----------------------------------------------------------------

class GameState:
    """Complete Battleship game state."""

    def __init__(self, first_attacker, num_rows, num_cols, fleet_spec):
        """
        first_attacker : PLAYER_1 or PLAYER_2 -- who fires first after placement.
        num_rows       : grid height.
        num_cols       : grid width.
        fleet_spec     : list of {"name": str, "count": int} dicts.
        """
        self.num_rows    = num_rows
        self.num_cols    = num_cols
        self.fleet_spec  = fleet_spec       # original spec kept for save/load
        self._flat_fleet = expand_fleet_spec(fleet_spec)
        self._next_ship_id = 1

        self.fleet_boards = {
            PLAYER_1: make_fleet_board(num_rows, num_cols),
            PLAYER_2: make_fleet_board(num_rows, num_cols),
        }
        self.attack_boards = {
            PLAYER_1: make_attack_board(num_rows, num_cols),
            PLAYER_2: make_attack_board(num_rows, num_cols),
        }
        self.ships = {PLAYER_1: [], PLAYER_2: []}

        self._placement_pending = {
            PLAYER_1: list(self._flat_fleet),
            PLAYER_2: list(self._flat_fleet),
        }

        self.first_attacker = first_attacker
        self.current_player = PLAYER_1
        self.phase          = PHASE_P1_PLACEMENT
        self.winner         = None
        self.game_over      = False

        # move_history entries: (player, row, col, result_str)
        # result_str is one of "hit", "miss", or "sunk:<ship name>"
        self.move_history = []

        logger.debug(
            "GameState init: %dx%d  fleet=%s  first_attacker=%d",
            num_cols, num_rows,
            [s["name"] for s in self._flat_fleet],
            first_attacker,
        )

    # -------------------------------------------------------------------------
    # Placement
    # -------------------------------------------------------------------------

    def placement_pending(self, player):
        """Return list of {name, size} dicts not yet placed for player."""
        return list(self._placement_pending[player])

    def all_placed(self, player):
        """True when player has placed every ship."""
        return len(self._placement_pending[player]) == 0

    def place_ship(self, player, row, col, shape, pending_idx=0):
        """
        Place the ship at pending_idx in the pending list for player at (row, col)
        using shape (a rotated variant of the ship's canonical shape).
        Returns the PlacedShip on success.
        Raises ValueError if placement is invalid or no ships remain.
        """
        pending = self._placement_pending[player]
        if not pending:
            raise ValueError("No ships left to place for player " + str(player))
        pending_idx = min(pending_idx, len(pending) - 1)
        spec = pending[pending_idx]
        if len(shape) != len(spec["shape"]):
            raise ValueError(
                "Shape size mismatch for " + spec["name"]
                + ": expected " + str(len(spec["shape"])) + " cells"
            )
        cells = ship_cells(row, col, shape, self.num_rows, self.num_cols)
        if not can_place_ship(self.fleet_boards[player], cells, self.num_rows, self.num_cols):
            raise ValueError(
                "Invalid placement for " + spec["name"]
                + " at (" + str(row) + "," + str(col) + ")"
            )
        ship = PlacedShip(self._next_ship_id, spec["name"], shape, cells)
        self._next_ship_id += 1
        _write_ship_to_board(self.fleet_boards[player], ship)
        self.ships[player].append(ship)
        pending.pop(pending_idx)
        self._placement_pending[player] = pending

        logger.debug(
            "P%d placed %s (id=%d) at (%d,%d) shape=%s",
            player, ship.name, ship.ship_id, row, col, shape,
        )

        # Advance phase when all ships placed
        if (not self._placement_pending[PLAYER_1]
                and not self._placement_pending[PLAYER_2]):
            self.phase          = (PHASE_P1_ATTACK if self.first_attacker == PLAYER_1
                                   else PHASE_P2_ATTACK)
            self.current_player = self.first_attacker
            logger.debug("Both fleets placed; moving to attack phase=%s", self.phase)
        elif (not self._placement_pending[PLAYER_1]
              and self.phase == PHASE_P1_PLACEMENT):
            self.phase          = PHASE_P2_PLACEMENT
            self.current_player = PLAYER_2
            logger.debug("P1 fleet done; moving to PHASE_P2_PLACEMENT")

        return ship

    def undo_last_ship(self, player):
        """
        Remove the most recently placed ship for player.
        Clears its cells from the fleet board and returns the spec
        ({"name", "shape"}) back to the front of the pending list.
        Returns the removed PlacedShip.
        Raises ValueError if no ships have been placed yet.
        """
        if not self.ships[player]:
            raise ValueError("No ships placed for player " + str(player))
        ship = self.ships[player].pop()
        for r, c in ship.cells:
            self.fleet_boards[player][r][c] = WATER
        self._placement_pending[player].insert(
            0, {"name": ship.name, "shape": ship.shape}
        )
        logger.debug("P%d undo: restored %s to pending", player, ship.name)
        return ship

    def clear_all_ships(self, player):
        """
        Remove every placed ship for player, reset the fleet board to water,
        and restore the full pending list.
        """
        self.ships[player] = []
        self.fleet_boards[player] = make_fleet_board(self.num_rows, self.num_cols)
        self._placement_pending[player] = list(self._flat_fleet)
        logger.debug("P%d fleet cleared", player)

    # -------------------------------------------------------------------------
    # Attack
    # -------------------------------------------------------------------------

    def attack(self, attacker, row, col):
        """
        Fire a shot at (row, col) as attacker.
        Returns AttackResult.
        Raises ValueError if the cell is already fired at or out of bounds.
        """
        if row < 0 or row >= self.num_rows or col < 0 or col >= self.num_cols:
            raise ValueError("Cell (" + str(row) + "," + str(col) + ") out of bounds")
        if self.attack_boards[attacker][row][col] != UNKNOWN:
            raise ValueError("Cell (" + str(row) + "," + str(col) + ") already fired at")

        opponent = OTHER_PLAYER[attacker]
        ship_id  = self.fleet_boards[opponent][row][col]
        hit      = (ship_id != WATER)

        self.attack_boards[attacker][row][col] = HIT_MARK if hit else MISS_MARK

        sunk_ship = None
        if hit:
            for s in self.ships[opponent]:
                if s.ship_id == ship_id:
                    s.receive_hit(row, col)
                    if s.is_sunk:
                        sunk_ship = s
                    break

        if sunk_ship is not None:
            result_str = "sunk:" + sunk_ship.name
        elif hit:
            result_str = "hit"
        else:
            result_str = "miss"

        self.move_history.append((attacker, row, col, result_str))
        logger.debug(
            "P%d fires at (%d,%d): %s", attacker, row, col, result_str
        )

        # Check win condition
        if all(s.is_sunk for s in self.ships[opponent]):
            self.winner    = attacker
            self.game_over = True
            self.phase     = PHASE_DONE
            logger.debug("P%d wins by sinking all opponent ships", attacker)
        else:
            next_player         = OTHER_PLAYER[attacker]
            self.current_player = next_player
            self.phase          = (PHASE_P1_ATTACK if next_player == PLAYER_1
                                   else PHASE_P2_ATTACK)

        return AttackResult(row, col, hit, sunk_ship)

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    def get_valid_attack_cells(self, attacker):
        """Return list of (row, col) not yet fired at by attacker."""
        board = self.attack_boards[attacker]
        return [
            (r, c)
            for r in range(self.num_rows)
            for c in range(self.num_cols)
            if board[r][c] == UNKNOWN
        ]

    def total_ship_cells(self, player):
        """Total number of ship cells in player's fleet."""
        return sum(len(s.cells) for s in self.ships[player])

    def remaining_ship_cells(self, player):
        """Number of un-hit ship cells remaining in player's fleet."""
        return sum(len(s.cells) - len(s.hits) for s in self.ships[player])

    def sunk_ships(self, player):
        """List of PlacedShip objects that have been sunk for the given player."""
        return [s for s in self.ships[player] if s.is_sunk]

    def compute_advantage_score(self):
        """
        Advantage score from Player 1's perspective.
        Positive = P1 is winning (has damaged more of P2's fleet proportionally).
        Returns an integer scaled by ADVANTAGE_SCALE.
        """
        total1 = self.total_ship_cells(PLAYER_1)
        total2 = self.total_ship_cells(PLAYER_2)
        if total1 == 0 or total2 == 0:
            return 0
        p1_damage = (total1 - self.remaining_ship_cells(PLAYER_1)) / total1
        p2_damage = (total2 - self.remaining_ship_cells(PLAYER_2)) / total2
        return int(ADVANTAGE_SCALE * (p2_damage - p1_damage))
