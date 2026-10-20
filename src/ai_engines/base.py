"""Abstract base class for all Battleship AI engine plugins."""
import logging
import random
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BattleshipAIEngine(ABC):
    """
    Plugin interface for Battleship AI engines.

    Each engine handles both fleet placement and attack selection.
    Subclass this class, implement the abstract methods, and provide a
    module-level factory function named create().

    The public methods place_ships() and next_attack() wrap the private
    implementations with input validation and automatic fallback so that
    the game can always continue even if an engine returns an invalid value.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Short human-readable identifier shown on the start screen and in logs."""

    def place_ships(self, num_rows, num_cols, flat_fleet):
        """
        Public entry point -- do NOT override in subclasses.

        Calls _compute_placement() and returns a list of (row, col, shape)
        tuples, one per entry in flat_fleet.  Falls back to random placement if
        the implementation returns None or a list of the wrong length.

        flat_fleet : list of {"name": str, "shape": list} dicts (already expanded
                     from the fleet spec -- one dict per ship instance).
        Returns    : list of (row, col, shape) tuples in the same order as
                     flat_fleet, where shape is a rotated variant of the
                     canonical ship shape.
        """
        placements = self._compute_placement(num_rows, num_cols, flat_fleet)
        if placements is None or len(placements) != len(flat_fleet):
            logger.warning(
                "%s._compute_placement returned bad result -- falling back to random",
                self.__class__.__name__,
            )
            placements = _random_placement(num_rows, num_cols, flat_fleet)
        return placements

    def next_attack(self, attack_board, num_rows, num_cols,
                    remaining_shapes=None, sunk_ships=None):
        """
        Public entry point -- do NOT override in subclasses.

        Calls _compute_next_attack() and validates the returned (row, col).
        Falls back to a random unknown cell if the implementation returns an
        invalid or already-fired cell.

        attack_board    : attack_board[row][col], 0=unknown, 1=miss, 2=hit
        num_rows        : grid height
        num_cols        : grid width
        remaining_shapes: list of shapes (each a list of [dr,dc]) for ships
                          not yet sunk (may be None)
        sunk_ships      : list of PlacedShip objects sunk so far (may be None)
        Returns         : (row, col) tuple for a cell that has not been fired at
        """
        valid = [
            (r, c)
            for r in range(num_rows)
            for c in range(num_cols)
            if attack_board[r][c] == 0
        ]
        if not valid:
            logger.error(
                "next_attack called with no valid cells -- returning (0, 0)"
            )
            return (0, 0)
        result = self._compute_next_attack(
            attack_board, num_rows, num_cols, remaining_shapes, sunk_ships
        )
        if result in valid:
            return result
        logger.warning(
            "%s._compute_next_attack returned invalid cell %s -- substituting random",
            self.__class__.__name__, result,
        )
        return random.choice(valid)

    @abstractmethod
    def _compute_placement(self, num_rows, num_cols, flat_fleet):
        """
        Compute ship placements for the entire fleet.

        flat_fleet : list of {"name": str, "shape": list} dicts in placement order.
        Returns    : list of (row, col, shape) tuples where shape is a rotated
                     variant (list of [dr,dc]) chosen for each ship.
        """

    @abstractmethod
    def _compute_next_attack(self, attack_board, num_rows, num_cols,
                              remaining_shapes, sunk_ships):
        """
        Compute the next cell to attack.

        attack_board    : attack_board[row][col], 0=unknown, 1=miss, 2=hit
        remaining_shapes: list of shapes for ships not yet sunk (or None)
        sunk_ships      : list of PlacedShip objects already sunk (or None)
        Returns         : (row, col) for a cell where attack_board == 0
        """

    @abstractmethod
    def reset(self):
        """Reset any internal state so the engine is ready for a fresh game."""


# ---------------------------------------------------------------------------
# Shared helper used by all engines that need random placement
# ---------------------------------------------------------------------------

def _random_placement(num_rows, num_cols, flat_fleet):
    """
    Place ships in random valid positions using random rotations.
    Used as both a default strategy and a fallback when an engine's
    _compute_placement() returns bad output.

    Returns a list of (row, col, shape) tuples in the same order as flat_fleet.
    """
    from game_logic import ship_cells, can_place_ship, make_fleet_board, get_all_rotations

    board  = make_fleet_board(num_rows, num_cols)
    result = []
    _MAX_TRIES = 1000

    for idx, spec in enumerate(flat_fleet):
        rotations = get_all_rotations(spec["shape"])
        placed = False
        for _ in range(_MAX_TRIES):
            shape = random.choice(rotations)
            r = random.randrange(num_rows)
            c = random.randrange(num_cols)
            cells = ship_cells(r, c, shape, num_rows, num_cols)
            if can_place_ship(board, cells, num_rows, num_cols):
                for rr, cc in cells:
                    board[rr][cc] = idx + 1
                result.append((r, c, shape))
                placed = True
                break
        if not placed:
            logger.error(
                "_random_placement could not place ship %s after %d tries",
                spec["name"], _MAX_TRIES,
            )
            result.append((0, 0, spec["shape"]))

    return result
