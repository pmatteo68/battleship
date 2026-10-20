"""
Save and load GameState to/from a human-readable JSON file.
No UI imports -- pure I/O logic.
"""
import json
import logging
from game_logic import (
    GameState, PlacedShip,
    PLAYER_1, PLAYER_2,
    PHASE_P1_PLACEMENT, PHASE_P2_PLACEMENT,
    PHASE_P1_ATTACK, PHASE_P2_ATTACK, PHASE_DONE,
    ATTACK_PHASES,
    make_fleet_board, make_attack_board,
)

logger = logging.getLogger(__name__)

FORMAT_VERSION = "2.0"
FILE_ENCODING  = "utf-8"

_VALID_PHASES = {
    PHASE_P1_PLACEMENT, PHASE_P2_PLACEMENT,
    PHASE_P1_ATTACK,    PHASE_P2_ATTACK,
    PHASE_DONE,
}
_VALID_PLAYERS = {PLAYER_1, PLAYER_2}


def save_game(state: GameState, human_player: "int | None", path: str) -> None:
    """
    Serialise state and the human player ID to a JSON file.
    human_player is PLAYER_1, PLAYER_2, or None (autoplay).
    """
    logger.debug("Saving game to '%s'", path)

    def _serialise_ships(ships):
        result = []
        for s in ships:
            result.append({
                "ship_id": s.ship_id,
                "name"   : s.name,
                "shape"  : [list(p) for p in s.shape],
                "cells"  : [list(c) for c in s.cells],
                "hits"   : [list(h) for h in s.hits],
            })
        return result

    data = {
        "format_version" : FORMAT_VERSION,
        "human_player"   : human_player,
        "num_rows"       : state.num_rows,
        "num_cols"       : state.num_cols,
        "fleet_spec"     : state.fleet_spec,
        "first_attacker" : state.first_attacker,
        "current_player" : state.current_player,
        "phase"          : state.phase,
        "winner"         : state.winner,
        "game_over"      : state.game_over,
        "move_history"   : [list(m) for m in state.move_history],
        "ships_p1"       : _serialise_ships(state.ships[PLAYER_1]),
        "ships_p2"       : _serialise_ships(state.ships[PLAYER_2]),
        "fleet_board_p1" : state.fleet_boards[PLAYER_1],
        "fleet_board_p2" : state.fleet_boards[PLAYER_2],
        "attack_board_p1": state.attack_boards[PLAYER_1],
        "attack_board_p2": state.attack_boards[PLAYER_2],
    }

    try:
        with open(path, "w", encoding=FILE_ENCODING) as fh:
            json.dump(data, fh, indent=2)
        logger.info("Game saved to '%s'", path)
    except Exception as exc:
        logger.error("Failed to save to '%s': %s", path, exc)
        raise


def load_game(path: str) -> "tuple[GameState, int | None]":
    """
    Load state from path. Returns (GameState, human_player).
    Raises ValueError on schema mismatch, IOError on file errors.
    """
    logger.debug("Loading game from '%s'", path)
    try:
        with open(path, "r", encoding=FILE_ENCODING) as fh:
            data = json.load(fh)
    except Exception as exc:
        logger.error("Failed to read '%s': %s", path, exc)
        raise

    _validate(data)

    state = GameState.__new__(GameState)
    state.num_rows     = int(data["num_rows"])
    state.num_cols     = int(data["num_cols"])
    state.fleet_spec   = data["fleet_spec"]

    from game_logic import expand_fleet_spec
    state._flat_fleet  = expand_fleet_spec(state.fleet_spec)

    state.first_attacker = int(data["first_attacker"])
    state.current_player = int(data["current_player"])
    state.phase          = data["phase"]
    state.winner         = data["winner"]
    state.game_over      = bool(data["game_over"])
    state.move_history   = [tuple(m) for m in data["move_history"]]

    state.fleet_boards = {
        PLAYER_1: [list(row) for row in data["fleet_board_p1"]],
        PLAYER_2: [list(row) for row in data["fleet_board_p2"]],
    }
    state.attack_boards = {
        PLAYER_1: [list(row) for row in data["attack_board_p1"]],
        PLAYER_2: [list(row) for row in data["attack_board_p2"]],
    }

    def _deserialise_ships(raw_list):
        ships = []
        for d in raw_list:
            s = PlacedShip(
                ship_id = int(d["ship_id"]),
                name    = d["name"],
                shape   = [list(p) for p in d["shape"]],
                cells   = [tuple(c) for c in d["cells"]],
            )
            s.hits = {tuple(h) for h in d["hits"]}
            ships.append(s)
        return ships

    state.ships = {
        PLAYER_1: _deserialise_ships(data["ships_p1"]),
        PLAYER_2: _deserialise_ships(data["ships_p2"]),
    }

    # Placement pending: empty if both sides have finished placing
    if state.phase in ATTACK_PHASES or state.phase == PHASE_DONE:
        state._placement_pending = {PLAYER_1: [], PLAYER_2: []}
    else:
        placed_p1 = len(state.ships[PLAYER_1])
        placed_p2 = len(state.ships[PLAYER_2])
        all_specs  = list(state._flat_fleet)
        state._placement_pending = {
            PLAYER_1: all_specs[placed_p1:],
            PLAYER_2: all_specs[placed_p2:],
        }

    # next_ship_id: max of all placed ship IDs + 1
    all_ids = ([s.ship_id for s in state.ships[PLAYER_1]]
               + [s.ship_id for s in state.ships[PLAYER_2]])
    state._next_ship_id = (max(all_ids) + 1) if all_ids else 1

    human_player = data.get("human_player")
    if human_player is not None:
        human_player = int(human_player)

    logger.info(
        "Game loaded from '%s' | phase=%s | moves=%d | human_player=%s",
        path, state.phase, len(state.move_history), human_player,
    )
    return state, human_player


def _validate(data: dict) -> None:
    if data.get("format_version") != FORMAT_VERSION:
        raise ValueError(
            "Unsupported format version: " + str(data.get("format_version"))
        )
    required = (
        "num_rows", "num_cols", "fleet_spec", "first_attacker",
        "current_player", "phase", "winner", "game_over",
        "move_history", "ships_p1", "ships_p2",
        "fleet_board_p1", "fleet_board_p2",
        "attack_board_p1", "attack_board_p2",
    )
    for key in required:
        if key not in data:
            raise ValueError("Missing field: '" + key + "'")
    if data["phase"] not in _VALID_PHASES:
        raise ValueError("Unknown phase: '" + str(data["phase"]) + "'")
    if data["current_player"] not in _VALID_PLAYERS:
        raise ValueError("Invalid current_player: " + str(data["current_player"]))
