"""
AI engine facade.
Loads the plugin named by config_game.AI_ENGINE and re-exports its contract.
The rest of the codebase imports only this module and never depends on a
specific engine implementation.
"""
import importlib
import logging
import config_game as CG

logger = logging.getLogger(__name__)

_engine = None


def _get():
    global _engine
    if _engine is None:
        path   = "ai_engines." + CG.AI_ENGINE
        logger.debug("Loading AI engine: %s", path)
        module  = importlib.import_module(path)
        _engine = module.create()
        logger.debug("AI engine loaded: %s", _engine.get_name())
    return _engine


def get_name() -> str:
    return _get().get_name()


def place_ships(num_rows: int, num_cols: int, flat_fleet: list) -> list:
    """Return a list of (row, col, shape) tuples, one per ship in flat_fleet."""
    return _get().place_ships(num_rows, num_cols, flat_fleet)


def next_attack(attack_board, num_rows: int, num_cols: int,
                remaining_shapes=None, sunk_ships=None):
    """Return (row, col) for the AI's next shot."""
    return _get().next_attack(
        attack_board, num_rows, num_cols, remaining_shapes, sunk_ships
    )


def reset() -> None:
    _get().reset()


def create_fresh_instance():
    """Return a new independent engine instance (own state, same algorithm).
    Use in autoplay mode so that both AI agents do not share state."""
    module = importlib.import_module("ai_engines." + CG.AI_ENGINE)
    return module.create()
