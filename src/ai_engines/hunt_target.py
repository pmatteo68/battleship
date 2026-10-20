"""
Hunt-and-Target Battleship AI engine with probability density.

Strategy overview
-----------------
Hunt mode (no active hit on an unsunk ship):
  Compute a probability density map: for every remaining ship size, count
  how many valid placements would cover each unknown cell (horizontally
  and vertically).  Fire at the highest-probability unknown cell.  When
  HUNT_MODE_CHECKERBOARD is True, break ties by preferring cells that also
  satisfy (row + col) % 2 == 0.

Target mode (one or more hits on a ship that has not been sunk yet):
  Collect all "active hits" -- HIT_MARK cells that are not part of any
  sunk ship.  If two or more active hits share a row or column, try the
  cells that extend the run first.  Otherwise try all four neighbours of
  every active hit.  Falls back to hunt mode if no valid neighbour exists.

Placement:
  Random valid placement (see _random_placement in base.py).
"""

import random
import logging

from .base import BattleshipAIEngine, _random_placement
from .hunt_target_config import (
    HUNT_MODE_CHECKERBOARD,
    PROBABILITY_DENSITY_ENABLED,
    TARGET_ADJACENT_PRIORITY,
)
from game_logic import HIT_MARK, MISS_MARK, UNKNOWN, get_all_rotations

logger = logging.getLogger(__name__)

_DIRS = ((0, 1), (0, -1), (1, 0), (-1, 0))


class HuntTargetEngine(BattleshipAIEngine):
    """Hunt-and-Target AI with optional probability density map."""

    def get_name(self) -> str:
        suffix = " (prob.density)" if PROBABILITY_DENSITY_ENABLED else ""
        return "Hunt & Target" + suffix

    def reset(self) -> None:
        logger.debug("HuntTargetEngine reset")

    def _compute_placement(self, num_rows, num_cols, flat_fleet):
        return _random_placement(num_rows, num_cols, flat_fleet)

    def _compute_next_attack(self, attack_board, num_rows, num_cols,
                              remaining_shapes, sunk_ships):
        # Collect cells of ships that are already sunk (their cells are known)
        sunk_cells = set()
        for s in (sunk_ships or []):
            sunk_cells.update(s.cells)

        # Active hits: HIT_MARK cells that do NOT belong to sunk ships
        active_hits = [
            (r, c)
            for r in range(num_rows)
            for c in range(num_cols)
            if attack_board[r][c] == HIT_MARK and (r, c) not in sunk_cells
        ]

        if active_hits:
            logger.debug("Target mode: %d active hits", len(active_hits))
            return self._target_mode(
                attack_board, num_rows, num_cols, active_hits, sunk_cells
            )

        logger.debug("Hunt mode")
        return self._hunt_mode(
            attack_board, num_rows, num_cols, remaining_shapes
        )

    # ------------------------------------------------------------------
    # Hunt mode
    # ------------------------------------------------------------------

    def _hunt_mode(self, attack_board, num_rows, num_cols, remaining_shapes):
        unknown = [
            (r, c)
            for r in range(num_rows)
            for c in range(num_cols)
            if attack_board[r][c] == UNKNOWN
        ]
        if not unknown:
            return (0, 0)

        if not PROBABILITY_DENSITY_ENABLED or not remaining_shapes:
            candidates = self._checkerboard_filter(unknown)
            return random.choice(candidates)

        # Build probability density map over all rotations of each remaining ship
        scores = {cell: 0 for cell in unknown}

        for shape in remaining_shapes:
            for rot_shape in get_all_rotations(shape):
                for r in range(num_rows):
                    for c in range(num_cols):
                        cells = [
                            (r + dr, c + dc)
                            for dr, dc in rot_shape
                        ]
                        if any(
                            rr < 0 or rr >= num_rows or cc < 0 or cc >= num_cols
                            for rr, cc in cells
                        ):
                            continue
                        if self._placement_fits(attack_board, cells):
                            for cell in cells:
                                if cell in scores:
                                    scores[cell] += 1

        max_score = max(scores.values(), default=0)
        best = [cell for cell, s in scores.items() if s == max_score]

        if HUNT_MODE_CHECKERBOARD:
            filtered = self._checkerboard_filter(best)
            if filtered:
                best = filtered

        return random.choice(best)

    @staticmethod
    def _placement_fits(attack_board, cells):
        """True if every cell in cells is UNKNOWN or HIT_MARK (not a miss)."""
        for r, c in cells:
            v = attack_board[r][c]
            if v == MISS_MARK:
                return False
        return True

    @staticmethod
    def _checkerboard_filter(cells):
        filtered = [(r, c) for r, c in cells if (r + c) % 2 == 0]
        return filtered if filtered else cells

    # ------------------------------------------------------------------
    # Target mode
    # ------------------------------------------------------------------

    def _target_mode(self, attack_board, num_rows, num_cols,
                     active_hits, sunk_cells):
        candidates = set()

        if len(active_hits) >= 2 and TARGET_ADJACENT_PRIORITY:
            rows = [r for r, c in active_hits]
            cols = [c for r, c in active_hits]

            if len(set(rows)) == 1:
                # Hits are in the same row -- extend horizontally
                r      = rows[0]
                min_c  = min(cols)
                max_c  = max(cols)
                for c in (min_c - 1, max_c + 1):
                    if 0 <= c < num_cols and attack_board[r][c] == UNKNOWN:
                        candidates.add((r, c))

            elif len(set(cols)) == 1:
                # Hits are in the same column -- extend vertically
                c      = cols[0]
                min_r  = min(rows)
                max_r  = max(rows)
                for r in (min_r - 1, max_r + 1):
                    if 0 <= r < num_rows and attack_board[r][c] == UNKNOWN:
                        candidates.add((r, c))

        # Fall back to all unknown neighbours if no directional extension found
        if not candidates:
            for r, c in active_hits:
                for dr, dc in _DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < num_rows and 0 <= nc < num_cols:
                        if (attack_board[nr][nc] == UNKNOWN
                                and (nr, nc) not in sunk_cells):
                            candidates.add((nr, nc))

        if not candidates:
            logger.debug("Target mode found no candidates -- falling back to hunt")
            return self._hunt_mode(attack_board, num_rows, num_cols, None)

        return random.choice(list(candidates))


def create() -> HuntTargetEngine:
    return HuntTargetEngine()
