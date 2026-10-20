"""In-game statistics collector for Battleship."""
import time
import logging
from game_logic import PLAYER_1, PLAYER_2, OTHER_PLAYER

logger = logging.getLogger(__name__)


class GameStats:

    def __init__(self):
        self._start_time           = time.monotonic()
        self._attack_phase_start   = None
        self._game_duration        = None
        self._attack_duration      = None

        self.winner                = None
        self.human_player          = None

        self._shots   = {PLAYER_1: 0, PLAYER_2: 0}
        self._hits    = {PLAYER_1: 0, PLAYER_2: 0}
        self._misses  = {PLAYER_1: 0, PLAYER_2: 0}
        self._sunk    = {PLAYER_1: 0, PLAYER_2: 0}

        self._placement_time = {PLAYER_1: 0.0, PLAYER_2: 0.0}

        # Advantage history: list of (move_number, score) tuples
        # move_number is 1-based total shot count; score from P1 perspective
        self._advantage_history: "list[tuple[int,int]]" = []

        # Progress history per player: list of (player_shot_number, pct) tuples
        # pct = hits / total_opponent_cells * 100  (0.0 .. 100.0)
        self._progress_history: "dict[int, list[tuple[int,float]]]" = {
            PLAYER_1: [], PLAYER_2: []
        }

        # Streak tracking
        self._current_streak  = {PLAYER_1: 0, PLAYER_2: 0}
        self._longest_streak  = {PLAYER_1: 0, PLAYER_2: 0}

        self._total_shots = 0

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_placement_time(self, player: int, seconds: float) -> None:
        self._placement_time[player] = seconds
        logger.debug("Stats: P%d placement time=%.2fs", player, seconds)

    def record_attack_phase_start(self) -> None:
        self._attack_phase_start = time.monotonic()
        logger.debug("Stats: attack phase started")

    def record_shot(self, player: int, result, state) -> None:
        """
        Call after each shot.
        result  : AttackResult
        state   : GameState (used to compute advantage score)
        """
        self._total_shots += 1
        self._shots[player] += 1

        if result.hit:
            self._hits[player]           += 1
            self._current_streak[player] += 1
            if self._current_streak[player] > self._longest_streak[player]:
                self._longest_streak[player] = self._current_streak[player]
        else:
            self._misses[player]         += 1
            self._current_streak[player]  = 0

        if result.sunk_ship is not None:
            self._sunk[player] += 1

        score = state.compute_advantage_score()
        self._advantage_history.append((self._total_shots, score))

        opponent_cells = state.total_ship_cells(OTHER_PLAYER[player])
        pct = self._hits[player] / opponent_cells * 100.0 if opponent_cells > 0 else 0.0
        self._progress_history[player].append((self._shots[player], pct))

        logger.debug(
            "Stats: shot #%d P%d (%d,%d) hit=%s sunk=%s score=%d",
            self._total_shots, player,
            result.row, result.col,
            result.hit, (result.sunk_ship.name if result.sunk_ship else None),
            score,
        )

    def finalise(self, winner: "int | None", human_player: "int | None") -> None:
        self._game_duration  = time.monotonic() - self._start_time
        self._attack_duration = (
            time.monotonic() - self._attack_phase_start
            if self._attack_phase_start is not None else 0.0
        )
        self.winner       = winner
        self.human_player = human_player
        self._log_summary()

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    def shots(self, player: int) -> int:
        return self._shots[player]

    def hits(self, player: int) -> int:
        return self._hits[player]

    def misses(self, player: int) -> int:
        return self._misses[player]

    def ships_sunk(self, player: int) -> int:
        return self._sunk[player]

    def accuracy(self, player: int) -> float:
        s = self._shots[player]
        return self._hits[player] / s if s else 0.0

    def longest_streak(self, player: int) -> int:
        return self._longest_streak[player]

    def placement_time(self, player: int) -> float:
        return self._placement_time[player]

    @property
    def attack_duration(self) -> float:
        return self._attack_duration or 0.0

    @property
    def game_duration(self) -> float:
        return self._game_duration or 0.0

    @property
    def advantage_history(self) -> "list[tuple[int,int]]":
        return list(self._advantage_history)

    def progress_history(self, player: int) -> "list[tuple[int,float]]":
        return list(self._progress_history[player])

    def get_summary_dict(self) -> dict:
        return {
            "shots_p1"          : self._shots[PLAYER_1],
            "shots_p2"          : self._shots[PLAYER_2],
            "hits_p1"           : self._hits[PLAYER_1],
            "hits_p2"           : self._hits[PLAYER_2],
            "misses_p1"         : self._misses[PLAYER_1],
            "misses_p2"         : self._misses[PLAYER_2],
            "accuracy_p1"       : self.accuracy(PLAYER_1),
            "accuracy_p2"       : self.accuracy(PLAYER_2),
            "ships_sunk_p1"     : self._sunk[PLAYER_1],
            "ships_sunk_p2"     : self._sunk[PLAYER_2],
            "longest_streak_p1" : self._longest_streak[PLAYER_1],
            "longest_streak_p2" : self._longest_streak[PLAYER_2],
            "placement_time_p1_s": self._placement_time[PLAYER_1],
            "placement_time_p2_s": self._placement_time[PLAYER_2],
            "attack_duration_s" : self.attack_duration,
            "total_duration_s"  : self.game_duration,
            "winner"            : self.winner,
            "advantage_history"    : list(self._advantage_history),
            "progress_history_p1"  : list(self._progress_history[PLAYER_1]),
            "progress_history_p2"  : list(self._progress_history[PLAYER_2]),
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_summary(self) -> None:
        dur = self.game_duration
        m, s = divmod(int(dur), 60)
        dur_str = (str(m) + "m" + str(s).zfill(2) + "s") if m else (str(s) + "s")

        w_str = ("Player " + str(self.winner)) if self.winner else "No winner"

        logger.info("=== BATTLESHIP GAME SUMMARY ===")
        logger.info("[OUTCOME] winner=%s  duration=%s", w_str, dur_str)
        logger.info(
            "[SHOTS] P1=%d (hits=%d misses=%d acc=%.1f%%)  "
            "P2=%d (hits=%d misses=%d acc=%.1f%%)",
            self._shots[PLAYER_1], self._hits[PLAYER_1],
            self._misses[PLAYER_1], self.accuracy(PLAYER_1) * 100,
            self._shots[PLAYER_2], self._hits[PLAYER_2],
            self._misses[PLAYER_2], self.accuracy(PLAYER_2) * 100,
        )
        logger.info(
            "[SUNK] P1 sank %d ships  P2 sank %d ships",
            self._sunk[PLAYER_1], self._sunk[PLAYER_2],
        )
        logger.info(
            "[STREAKS] P1 longest=%d  P2 longest=%d",
            self._longest_streak[PLAYER_1], self._longest_streak[PLAYER_2],
        )
        logger.info(
            "[TIMING] placement P1=%.1fs P2=%.1fs  attack=%.1fs",
            self._placement_time[PLAYER_1],
            self._placement_time[PLAYER_2],
            self.attack_duration,
        )
