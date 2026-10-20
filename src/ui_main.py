"""Main application window and controller for Battleship."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import time

import config_game    as CG
import config_text    as CT
import config_ui      as UI
import ai_engine      as AE
from game_logic        import (
    GameState, PLAYER_1, PLAYER_2, OTHER_PLAYER,
    PHASE_P1_PLACEMENT, PHASE_P2_PLACEMENT,
    PHASE_P1_ATTACK, PHASE_P2_ATTACK,
    PHASE_DONE, ATTACK_PHASES,
    WATER, HIT_MARK, MISS_MARK, UNKNOWN,
    expand_fleet_spec,
)
from game_persistence  import save_game, load_game
from game_stats        import GameStats
from ui_board          import GridCanvas, BattleshipBoard, PlacementPanel
from ui_stats          import StatsWindow

log = logging.getLogger(__name__)

_FIRST_HUMAN = "human"
_FIRST_AI    = "ai"


def _player_label(player: int, human_player: "int | None") -> str:
    """Return the display name for player based on game mode."""
    if human_player is None:
        return CT.PLAYER_1_NAME if player == PLAYER_1 else CT.PLAYER_2_NAME
    return CT.PLAYER_HUMAN if player == human_player else CT.PLAYER_AI


# ---------------------------------------------------------------------------
# Fleet preview dialog
# ---------------------------------------------------------------------------

class FleetPreviewDialog:
    """
    Modal dialog that shows one canonical shape for each ship type in the
    currently selected fleet preset.  Opened from the '?' button on the
    start screen.
    """

    def __init__(self, parent: tk.Widget, preset_name: str) -> None:
        import config_ships as CS
        from game_logic import normalize_shape

        s = UI

        top = tk.Toplevel(parent)
        top.withdraw()   # hide until positioned
        top.title(CT.FLEET_PREVIEW_TITLE.format(preset=preset_name))
        top.transient(parent)
        top.resizable(False, False)
        top.configure(bg=s.BG_COLOR)

        tk.Label(
            top,
            text=CT.FLEET_PREVIEW_TITLE.format(preset=preset_name),
            font=s.HEADER_FONT, fg=s.TEXT_COLOR, bg=s.BG_COLOR,
        ).pack(pady=(14, 2), padx=20)

        tk.Label(
            top,
            text=CT.FLEET_PREVIEW_SUBTITLE,
            font=s.STATUS_FONT, fg=s.TEXT_SECONDARY, bg=s.BG_COLOR,
        ).pack(pady=(0, 8), padx=20)

        fleet_spec = CG.FLEET_PRESETS.get(preset_name,
                                          CG.FLEET_PRESETS[CG.FLEET_PRESET_DEFAULT])

        # Build unique types in fleet order, with total count per type
        seen = []
        counts = {}
        for spec in fleet_spec:
            nm = spec["name"]
            counts[nm] = counts.get(nm, 0) + spec["count"]
            if nm not in seen:
                seen.append(nm)

        cell_px = s.FLEET_PREVIEW_CELL_SIZE
        gap     = s.FLEET_PREVIEW_CELL_GAP
        box_w   = s.FLEET_PREVIEW_BOX_W
        box_h   = s.FLEET_PREVIEW_BOX_H
        row_pad = s.FLEET_PREVIEW_ROW_PADY

        container = tk.Frame(top, bg=s.BG_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=4)

        for nm in seen:
            shape = normalize_shape(CS.SHIP_TYPES[nm])
            count = counts[nm]

            row_frame = tk.Frame(container, bg=s.BG_COLOR)
            row_frame.pack(fill="x", pady=row_pad)

            max_r = max(r for r, c in shape)
            max_c = max(c for r, c in shape)
            shape_w = (max_c + 1) * cell_px
            shape_h = (max_r + 1) * cell_px
            off_x = (box_w - shape_w) // 2
            off_y = (box_h - shape_h) // 2

            canv = tk.Canvas(row_frame, width=box_w, height=box_h,
                             bg=s.BG_COLOR, highlightthickness=0)
            canv.pack(side="left", padx=(0, 14))

            for dr, dc in shape:
                x1 = off_x + dc * cell_px
                y1 = off_y + dr * cell_px
                x2 = x1 + cell_px - gap
                y2 = y1 + cell_px - gap
                canv.create_rectangle(x1, y1, x2, y2,
                                      fill=s.SHIP_COLOR, outline=s.BG_COLOR)

            size = len(shape)
            tk.Label(
                row_frame,
                text=str(count) + " x  " + nm + "  (" + str(size) + " cells)",
                font=s.STATUS_FONT, fg=s.TEXT_COLOR, bg=s.BG_COLOR,
                anchor="w",
            ).pack(side="left", fill="x")

        tk.Button(
            top, text=CT.BTN_CLOSE,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            command=top.destroy,
        ).pack(pady=(8, 16), padx=20)

        # Position just to the right of the splash window, vertically centred
        top.update_idletasks()
        par_win = parent.winfo_toplevel()
        px = par_win.winfo_rootx()
        py = par_win.winfo_rooty()
        pw = par_win.winfo_width()
        ph = par_win.winfo_height()
        dw = top.winfo_width()
        dh = top.winfo_height()
        x  = px + pw + s.FLEET_PREVIEW_OFFSET_X
        y  = py + max(0, (ph - dh) // 2)
        top.geometry("+" + str(x) + "+" + str(y))
        top.deiconify()
        top.grab_set()

        parent.wait_window(top)


# ---------------------------------------------------------------------------
# Start screen
# ---------------------------------------------------------------------------

class StartScreen(tk.Frame):
    """Initial screen with game parameter selection and mode buttons."""

    def __init__(self, parent, on_start, on_load, on_quit, on_autoplay):
        super().__init__(parent, bg=UI.BG_COLOR)
        self._on_start       = on_start
        self._on_load        = on_load
        self._on_quit        = on_quit
        self._on_autoplay_cb = on_autoplay
        self._build()

    def _build(self) -> None:
        s = UI

        tk.Label(self, text=CT.START_TITLE,
                 font=s.START_TITLE_FONT, fg=s.START_TITLE_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_TITLE_PADY, 0))

        tk.Label(self, text=CT.START_SUBTITLE,
                 font=s.START_SUBTITLE_FONT, fg=s.START_SUBTITLE_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_SUBTITLE_PADY, 0))

        tk.Label(self, text=CT.START_ENGINE_LABEL + "  " + AE.get_name(),
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR,
                 bg=s.BG_COLOR).pack(pady=(2, 0))

        # Parameter grid
        grid_frame = tk.Frame(self, bg=s.BG_COLOR)
        grid_frame.pack(pady=(s.START_SECTION_PADY, 0))

        self._rows_var  = tk.StringVar(value=str(CG.GRID_ROWS_DEFAULT))
        self._cols_var  = tk.StringVar(value=str(CG.GRID_COLS_DEFAULT))
        self._fleet_var = tk.StringVar(value=CG.FLEET_PRESET_DEFAULT)

        rows_opts  = [str(v) for v in range(CG.GRID_ROWS_MIN, CG.GRID_ROWS_MAX + 1)]
        cols_opts  = [str(v) for v in range(CG.GRID_COLS_MIN, CG.GRID_COLS_MAX + 1)]
        fleet_opts = list(CG.FLEET_PRESET_NAMES)

        params = [
            (CT.START_ROWS_LABEL,  self._rows_var,  rows_opts),
            (CT.START_COLS_LABEL,  self._cols_var,  cols_opts),
            (CT.START_FLEET_LABEL, self._fleet_var, fleet_opts),
        ]
        for idx, (label, var, opts) in enumerate(params):
            tk.Label(grid_frame, text=label, font=s.LABEL_FONT,
                     fg=s.LABEL_COLOR, bg=s.BG_COLOR,
                     anchor="e").grid(row=idx, column=0, sticky="e",
                                      padx=(0, 8), pady=3)
            om = tk.OptionMenu(grid_frame, var, *opts)
            om.config(bg=s.BTN_BG, fg=s.BTN_FG,
                      activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                      highlightthickness=0, font=s.BTN_FONT,
                      relief=s.BTN_RELIEF, bd=s.MENU_BD, width=12)
            om["menu"].config(bg=s.BTN_BG, fg=s.BTN_FG,
                              activebackground=s.BTN_ACTIVE_BG,
                              activeforeground=s.BTN_FG)
            om.grid(row=idx, column=1, sticky="w", pady=3)

        # Fleet preview button -- column 2 of the fleet preset row (idx=2)
        tk.Button(
            grid_frame, text=CT.BTN_FLEET_PREVIEW,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            command=self._show_fleet_preview,
        ).grid(row=2, column=2, padx=(6, 0), pady=3)

        # Who attacks first
        tk.Label(self, text=CT.START_WHO_FIRST,
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_WHO_FIRST_PADY, 0))

        radio_frame = tk.Frame(self, bg=s.BG_COLOR)
        radio_frame.pack()

        self._first_var = tk.StringVar(value=CG.DEFAULT_FIRST_PLAYER)
        for value, text in ((_FIRST_HUMAN, CT.START_FIRST_HUMAN),
                             (_FIRST_AI,    CT.START_FIRST_AI)):
            tk.Radiobutton(
                radio_frame, text=text,
                variable=self._first_var, value=value,
                font=s.BTN_FONT, fg=s.LABEL_COLOR, bg=s.BG_COLOR,
                activebackground=s.BG_COLOR, selectcolor=s.BG_COLOR,
            ).pack(side="left", padx=s.START_BTN_PADX)

        # Buttons
        for text, cmd in (
            (CT.BTN_START,    self._on_start_clicked),
            (CT.BTN_LOAD_GAME, self._on_load),
            (CT.BTN_AUTOPLAY, self._on_autoplay_clicked),
            (CT.BTN_QUIT,     self._on_quit),
        ):
            tk.Button(
                self, text=text,
                font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
                activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                relief=s.BTN_RELIEF, bd=s.BTN_BD,
                padx=s.BTN_PADX, pady=s.BTN_PADY,
                command=cmd,
            ).pack(pady=(s.START_BOTTOM_ROW_PADY // 2, 0),
                   padx=s.START_BTN_PADX, fill="x", ipadx=10)

    def _on_start_clicked(self) -> None:
        try:
            self._on_start(
                int(self._rows_var.get()),
                int(self._cols_var.get()),
                self._fleet_var.get(),
                self._first_var.get(),
            )
        except (ValueError, tk.TclError) as exc:
            log.error("Start screen bad input: %s", exc)

    def _show_fleet_preview(self) -> None:
        FleetPreviewDialog(self, self._fleet_var.get())

    def _on_autoplay_clicked(self) -> None:
        try:
            self._on_autoplay_cb(
                int(self._rows_var.get()),
                int(self._cols_var.get()),
                self._fleet_var.get(),
            )
        except (ValueError, tk.TclError) as exc:
            log.error("Auto play bad input: %s", exc)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class App(tk.Tk):
    """Top-level window. Manages phases, AI threads, and board widgets."""

    def __init__(self):
        super().__init__()
        self.title(CT.WINDOW_TITLE)
        self.configure(bg=UI.BG_COLOR)
        self.resizable(False, False)

        self._gs            : "GameState | None"  = None
        self._human_player  : "int | None"        = None
        self._stats         : "GameStats | None"  = None
        self._autoplay      = False
        self._game_id       = 0
        self._min_width     = 0

        # AI engine instances
        self._ai_engine     = None   # single AI engine for HvAI
        self._autoplay_engines: "dict[int, object]" = {}

        # Active widgets (vary by phase)
        self._start_frame        : "StartScreen | None"    = None
        self._game_frame         : "tk.Frame | None"       = None
        self._placement_frame    : "tk.Frame | None"       = None
        self._placement_panel    : "PlacementPanel | None" = None
        self._battleship_board   : "BattleshipBoard | None"= None
        self._status_label       : "tk.Label | None"       = None

        # Placement timing
        self._placement_start_time: "dict[int, float]" = {}

        self._build_menu()
        self._show_start()

    # ------------------------------------------------------------------
    # Screen management
    # ------------------------------------------------------------------

    def _show_start(self) -> None:
        log.debug("Navigating to start screen")
        self._min_width = 0
        self._teardown_game()
        if self._start_frame:
            self._start_frame.destroy()
        self._start_frame = StartScreen(
            self, self._on_start_normal,
            self._on_load_game, self.quit,
            self._on_start_autoplay,
        )
        self._start_frame.pack(fill="both", expand=True,
                                padx=UI.BOARD_PADDING, pady=UI.BOARD_PADDING)
        self.after(UI.LAYOUT_INIT_DELAY_MS, self._fit_window)

    def _show_game(self, state: GameState, human_player: "int | None") -> None:
        log.debug("Navigating to game screen hp=%s autoplay=%s",
                  human_player, self._autoplay)
        if self._start_frame:
            self._start_frame.pack_forget()
            self._start_frame.destroy()
            self._start_frame = None
        self._teardown_game()

        self._gs           = state
        self._human_player = human_player
        self._stats        = GameStats()
        self._game_id     += 1
        self._placement_start_time = {}

        if self._autoplay:
            self._ai_engine = None
            self._autoplay_engines = {
                PLAYER_1: AE.create_fresh_instance(),
                PLAYER_2: AE.create_fresh_instance(),
            }
            log.debug("Autoplay: created AI engine for both players")
        else:
            self._autoplay_engines = {}
            self._ai_engine = AE.create_fresh_instance()
            AE.reset()

        self._min_width  = UI.MIN_WINDOW_WIDTH
        self._game_frame = tk.Frame(self, bg=UI.BG_COLOR)
        self._game_frame.pack(fill="both", expand=True)

        self._build_status_bar(self._game_frame)
        self.after(UI.LAYOUT_INIT_DELAY_MS, self._fit_window)

        if state.game_over:
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._on_loaded_game_over)
        elif state.phase in ATTACK_PHASES or state.phase == PHASE_DONE:
            self._setup_attack_phase()
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._begin_attack_turn)
        else:
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._begin_placement)

    def _teardown_game(self) -> None:
        if self._game_frame:
            self._game_frame.destroy()
            self._game_frame       = None
            self._placement_frame  = None
            self._placement_panel  = None
            self._battleship_board = None
            self._status_label     = None
        self._gs                  = None
        self._ai_engine           = None
        self._autoplay_engines    = {}

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _build_status_bar(self, parent: tk.Frame) -> None:
        s = UI
        bar = tk.Frame(parent, bg=s.STATUS_BG, height=s.STATUS_BAR_HEIGHT)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        btn_frame = tk.Frame(bar, bg=s.STATUS_BG)
        btn_frame.pack(side="right", padx=s.STATUS_BTN_PADX_END,
                       pady=s.STATUS_BTN_PADY)

        for label, cmd in (
            (CT.BTN_NEW_GAME,  self._on_new_game),
            (CT.BTN_SAVE_GAME, self._on_save_game),
            (CT.BTN_LOAD_GAME, self._on_load_game),
            (CT.BTN_QUIT,      self.quit),
        ):
            tk.Button(
                btn_frame, text=label,
                font=s.STATUS_BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
                activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                relief=s.BTN_RELIEF, bd=s.BTN_BD,
                padx=s.STATUS_BTN_PADX, pady=s.STATUS_BTN_PADY,
                command=cmd,
            ).pack(side="left", padx=s.STATUS_BTN_PADX // 2)

        self._status_label = tk.Label(
            bar, text="",
            font=s.STATUS_FONT, fg=s.STATUS_COLOR, bg=s.STATUS_BG,
            anchor="w", padx=s.STATUS_LABEL_PADX,
        )
        self._status_label.pack(side="left", fill="x", expand=True)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        s = UI
        menubar = tk.Menu(self, bg=s.BG_COLOR, fg=s.MENU_FG,
                          activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                          bd=s.MENU_BD)

        game_menu = tk.Menu(menubar, tearoff=0, bg=s.BG_COLOR, fg=s.MENU_FG,
                            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG)
        game_menu.add_command(label=CT.MENU_NEW,  command=self._on_new_game)
        game_menu.add_command(label=CT.MENU_SAVE, command=self._on_save_game)
        game_menu.add_command(label=CT.MENU_LOAD, command=self._on_load_game)
        game_menu.add_separator()
        game_menu.add_command(label=CT.MENU_QUIT, command=self.quit)
        menubar.add_cascade(label=CT.MENU_GAME, menu=game_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=s.BG_COLOR, fg=s.MENU_FG,
                            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG)
        help_menu.add_command(label=CT.MENU_RULES, command=self._show_rules)
        help_menu.add_command(label=CT.MENU_ABOUT, command=self._show_about)
        menubar.add_cascade(label=CT.MENU_HELP, menu=help_menu)
        self.config(menu=menubar)

    # ------------------------------------------------------------------
    # Placement phase
    # ------------------------------------------------------------------

    def _begin_placement(self) -> None:
        if self._gs is None:
            return
        if self._gs.phase == PHASE_P1_PLACEMENT:
            self._begin_placement_p1()
        elif self._gs.phase == PHASE_P2_PLACEMENT:
            self._begin_placement_p2()

    def _begin_placement_p1(self) -> None:
        if self._gs is None:
            return
        self._placement_start_time[PLAYER_1] = time.monotonic()
        log.debug("Starting P1 placement phase; autoplay=%s", self._autoplay)

        if self._autoplay:
            self._set_status(CT.STATUS_AI_PLACING)
            engine = self._autoplay_engines[PLAYER_1]
            self._start_ai_placement(PLAYER_1, engine, self._game_id,
                                     self._on_p1_placement_done)
        else:
            self._set_status(
                CT.STATUS_PLACEMENT_FMT.format(
                    name=_player_label(PLAYER_1, self._human_player)),
                PLAYER_1)
            self._show_placement_panel(PLAYER_1)

    def _begin_placement_p2(self) -> None:
        if self._gs is None:
            return
        self._placement_start_time[PLAYER_2] = time.monotonic()
        log.debug("Starting P2 placement phase")
        self._set_status(CT.STATUS_AI_PLACING)
        engine = (self._autoplay_engines[PLAYER_2]
                  if self._autoplay else self._ai_engine)
        self._start_ai_placement(PLAYER_2, engine, self._game_id,
                                 self._on_p2_placement_done)

    def _show_placement_panel(self, player: int) -> None:
        """Display PlacementPanel for a human player."""
        if self._gs is None or self._game_frame is None:
            return
        s = UI

        if self._placement_panel:
            self._placement_panel.destroy()
            self._placement_panel = None

        title_text = CT.PLACEMENT_TITLE_FMT.format(
            name=_player_label(player, self._human_player))
        frame = tk.Frame(self._game_frame, bg=s.BG_COLOR)
        frame.pack(fill="both", expand=True,
                   padx=s.BOARD_PADDING, pady=s.BOARD_PADDING)
        self._placement_frame = frame

        tk.Label(frame, text=title_text,
                 font=s.HEADER_FONT, fg=s.TEXT_COLOR,
                 bg=s.BG_COLOR).pack(pady=(0, s.PAD_Y))

        flat_fleet = list(self._gs.placement_pending(player))
        panel = PlacementPanel(
            frame,
            self._gs.num_rows,
            self._gs.num_cols,
            flat_fleet,
            on_confirm    = self._on_human_confirm_fleet,
            on_random     = lambda: self._on_human_random_fleet(player),
            on_ship_select= None,
            on_undo       = lambda: self._on_human_undo_placement(player),
            on_clear      = lambda: self._on_human_clear_fleet(player),
        )
        panel.set_click_handler(
            lambda r, c, shape, idx: self._on_human_place_click(player, r, c, shape, idx)
        )
        panel.pack(fill="both", expand=True)
        self._placement_panel = panel
        self.after(UI.LAYOUT_INIT_DELAY_MS, self._fit_window)

    def _on_human_place_click(self, player: int, row: int, col: int,
                               shape: list, pending_idx: int = 0) -> None:
        if self._gs is None or self._placement_panel is None:
            return
        pending = self._gs.placement_pending(player)
        if not pending:
            return
        pending_idx = min(pending_idx, len(pending) - 1)
        from game_logic import ship_cells, can_place_ship
        cells = ship_cells(row, col, shape,
                           self._gs.num_rows, self._gs.num_cols)
        if not can_place_ship(self._gs.fleet_boards[player], cells,
                               self._gs.num_rows, self._gs.num_cols):
            return
        try:
            self._gs.place_ship(player, row, col, shape, pending_idx)
            self._placement_panel.mark_ship_placed(cells)
            remaining = self._gs.placement_pending(player)
            if remaining:
                self._set_status(
                    CT.STATUS_PLACE_SHIP.format(
                        name=remaining[0]["name"],
                        size=len(remaining[0]["shape"]),
                    ),
                    player,
                )
            else:
                self._set_status(CT.STATUS_FLEET_READY, player)
            log.debug("Human P%d placed ship at (%d,%d) shape=%s",
                      player, row, col, shape)
        except ValueError as exc:
            log.debug("Invalid placement: %s", exc)

    def _on_human_random_fleet(self, player: int) -> None:
        if self._gs is None or self._placement_panel is None:
            return
        engine = self._ai_engine or AE.create_fresh_instance()
        pending = self._gs.placement_pending(player)
        placements = engine.place_ships(
            self._gs.num_rows, self._gs.num_cols, list(pending)
        )
        # Reset board to just-initialized state
        from game_logic import make_fleet_board
        self._gs.fleet_boards[player] = make_fleet_board(
            self._gs.num_rows, self._gs.num_cols
        )
        self._gs.ships[player] = []
        self._gs._placement_pending[player] = list(self._gs._flat_fleet)
        self._gs._next_ship_id = 1

        for i, (r, c, shape) in enumerate(placements):
            try:
                self._gs.place_ship(player, r, c, shape)
            except ValueError:
                pass

        self._placement_panel.set_fleet_board(self._gs.fleet_boards[player])
        # Sync the flat_fleet list in the panel
        self._placement_panel._flat_fleet = list(self._gs.placement_pending(player))
        self._placement_panel._selected_idx = 0
        self._placement_panel._refresh_table()
        self._placement_panel._update_rotations()
        something_placed = not self._gs.placement_pending(player)  # all placed = random filled all
        any_placed = len(self._gs.ships[player]) > 0
        btn_state = "normal" if any_placed else "disabled"
        self._placement_panel._undo_btn.config(state=btn_state)
        self._placement_panel._clear_btn.config(state=btn_state)
        if self._gs.all_placed(player):
            self._placement_panel._confirm_btn.config(state="normal")
            self._set_status(CT.STATUS_FLEET_READY, player)
        log.debug("Human P%d random placement done", player)

    def _on_human_undo_placement(self, player: int) -> None:
        if self._gs is None or self._placement_panel is None:
            return
        try:
            ship = self._gs.undo_last_ship(player)
            self._placement_panel.restore_ship(
                {"name": ship.name, "shape": ship.shape}, ship.cells
            )
            pending = self._gs.placement_pending(player)
            self._set_status(
                CT.STATUS_PLACE_SHIP.format(
                    name=pending[0]["name"],
                    size=len(pending[0]["shape"]),
                ),
                player,
            )
            log.debug("Human P%d undid placement of %s", player, ship.name)
        except ValueError as exc:
            log.debug("Undo failed: %s", exc)

    def _on_human_clear_fleet(self, player: int) -> None:
        if self._gs is None or self._placement_panel is None:
            return
        self._gs.clear_all_ships(player)
        self._placement_panel.restore_all()
        pending = self._gs.placement_pending(player)
        if pending:
            self._set_status(
                CT.STATUS_PLACE_SHIP.format(
                    name=pending[0]["name"],
                    size=len(pending[0]["shape"]),
                ),
                player,
            )
        log.debug("Human P%d cleared entire fleet", player)

    def _on_human_confirm_fleet(self) -> None:
        if self._gs is None or self._placement_panel is None:
            return
        if not self._gs.all_placed(PLAYER_1):
            return
        elapsed = time.monotonic() - self._placement_start_time.get(PLAYER_1, 0)
        self._stats.record_placement_time(PLAYER_1, elapsed)
        log.debug("P1 fleet confirmed; timing=%.1fs", elapsed)

        if self._placement_panel:
            self._placement_panel.destroy()
            self._placement_panel = None

        # Move to P2 placement (always AI in HvAI mode)
        self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._begin_placement_p2)

    def _on_p1_placement_done(self) -> None:
        if self._gs is None:
            return
        elapsed = time.monotonic() - self._placement_start_time.get(PLAYER_1, 0)
        self._stats.record_placement_time(PLAYER_1, elapsed)
        log.debug("P1 placement done (autoplay)")
        # In autoplay both fleets are placed back to back
        self.after(CG.AUTOPLAY_HANDOFF_SPLASH_MS, self._begin_placement_p2)

    def _on_p2_placement_done(self) -> None:
        if self._gs is None:
            return
        elapsed = time.monotonic() - self._placement_start_time.get(PLAYER_2, 0)
        self._stats.record_placement_time(PLAYER_2, elapsed)
        log.debug("P2 placement done; transitioning to attack phase")
        self._setup_attack_phase()
        self._stats.record_attack_phase_start()
        self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._begin_attack_turn)

    # ------------------------------------------------------------------
    # AI placement helpers
    # ------------------------------------------------------------------

    def _start_ai_placement(self, player: int, engine,
                             game_id: int, on_done) -> None:
        if self._gs is None:
            return
        pending = list(self._gs.placement_pending(player))
        num_r   = self._gs.num_rows
        num_c   = self._gs.num_cols

        def _run():
            placements = engine.place_ships(num_r, num_c, pending)
            self.after(0, lambda: self._on_ai_placements_ready(
                player, placements, game_id, on_done))

        threading.Thread(target=_run, daemon=True,
                         name="AI-place-P" + str(player)).start()

    def _on_ai_placements_ready(self, player: int, placements: list,
                                  game_id: int, on_done) -> None:
        if game_id != self._game_id:
            return
        self._place_ships_sequentially(player, placements, 0, on_done)

    def _place_ships_sequentially(self, player: int, placements: list,
                                   idx: int, on_done) -> None:
        if self._gs is None or self._game_id != self._game_id:
            return
        if idx >= len(placements):
            on_done()
            return
        r, c, shape = placements[idx]
        try:
            self._gs.place_ship(player, r, c, shape)
            log.debug("AI P%d placed ship #%d at (%d,%d) shape=%s",
                      player, idx + 1, r, c, shape)
        except ValueError as exc:
            log.warning("AI placement error at idx=%d: %s", idx, exc)

        delay = (CG.AUTOPLAY_PLACEMENT_DELAY_MS if self._autoplay
                 else CG.AI_PLACEMENT_DELAY_MS)
        self.after(delay,
                   lambda: self._place_ships_sequentially(
                       player, placements, idx + 1, on_done))

    # ------------------------------------------------------------------
    # Attack phase setup
    # ------------------------------------------------------------------

    def _setup_attack_phase(self) -> None:
        if self._gs is None or self._game_frame is None:
            return
        s = UI

        if self._placement_frame:
            self._placement_frame.destroy()
            self._placement_frame = None
            self._placement_panel = None

        # Choose which player's perspective to display
        # HvAI: always show human player's perspective
        # Autoplay: show PLAYER_1's perspective
        view_player = self._human_player if self._human_player else PLAYER_1

        if self._human_player is not None:
            left_label  = CT.LABEL_YOUR_FLEET
            right_label = CT.LABEL_ENEMY_WATERS
        elif view_player == PLAYER_1:
            left_label  = CT.LABEL_P1_FLEET
            right_label = CT.LABEL_P1_ATTACKS
        else:
            left_label  = CT.LABEL_P2_FLEET
            right_label = CT.LABEL_P2_ATTACKS

        p1_name = _player_label(PLAYER_1, self._human_player)
        p2_name = _player_label(PLAYER_2, self._human_player)

        board_frame = tk.Frame(self._game_frame, bg=s.BG_COLOR)
        board_frame.pack(fill="both", expand=True,
                         padx=s.BOARD_PADDING, pady=s.BOARD_PADDING)

        on_click = (self._on_human_attack_click
                    if (not self._autoplay and view_player == self._human_player)
                    else None)

        self._battleship_board = BattleshipBoard(
            board_frame,
            self._gs.num_rows,
            self._gs.num_cols,
            left_label, right_label,
            fleet_spec=self._gs.fleet_spec,
            p1_name=p1_name,
            p2_name=p2_name,
            stats_position=CG.STATS_PANEL_POSITION,
            on_attack_click=on_click,
        )
        self._battleship_board.pack()

        self._view_player = view_player
        self._refresh_attack_boards()
        self.after(UI.LAYOUT_INIT_DELAY_MS, self._fit_window)

    def _refresh_attack_boards(self) -> None:
        if self._gs is None or self._battleship_board is None:
            return
        vp = self._view_player
        op = OTHER_PLAYER[vp]

        # Fleet board: own ship positions + received hits
        self._render_fleet_grid(vp)
        # Attack board: own shots at opponent
        self._battleship_board.update_attack_board(self._gs.attack_boards[vp])
        # Live stats row
        self._update_live_stats()

    def _update_live_stats(self) -> None:
        if self._gs is None or self._battleship_board is None or self._stats is None:
            return
        self._battleship_board.update_live_stats(self._gs, self._stats)

    def _render_fleet_grid(self, player: int) -> None:
        """Render player's fleet grid: ships + hit overlay from opponent attacks."""
        if self._gs is None or self._battleship_board is None:
            return
        s  = UI
        op = OTHER_PLAYER[player]
        op_attack = self._gs.attack_boards[op]
        fleet     = self._gs.fleet_boards[player]
        num_r     = self._gs.num_rows
        num_c     = self._gs.num_cols

        # Build hit cell set from opponent's attack board
        hit_cells  = set()
        miss_cells = set()
        for r in range(num_r):
            for c in range(num_c):
                if op_attack[r][c] == HIT_MARK:
                    hit_cells.add((r, c))
                elif op_attack[r][c] == MISS_MARK:
                    miss_cells.add((r, c))

        sunk_cells = set()
        for ship in self._gs.sunk_ships(player):
            sunk_cells.update(ship.cells)

        self._battleship_board.fleet_grid.clear_all_marks()
        for r in range(num_r):
            for c in range(num_c):
                cell = (r, c)
                if cell in sunk_cells:
                    color = s.SUNK_COLOR
                elif cell in hit_cells:
                    color = s.HIT_COLOR
                elif fleet[r][c] != WATER:
                    color = s.SHIP_COLOR
                else:
                    color = s.FLEET_WATER_COLOR
                self._battleship_board.fleet_grid.set_cell_color(r, c, color)

        if CG.SHOW_OPPONENT_MISSES:
            for r, c in miss_cells:
                self._battleship_board.fleet_grid.set_cell_mark(
                    r, c, CT.FLEET_MISS_MARK_TEXT, s.FLEET_MISS_MARK_COLOR
                )

    # ------------------------------------------------------------------
    # Attack phase -- human turn
    # ------------------------------------------------------------------

    def _begin_attack_turn(self) -> None:
        if self._gs is None or self._gs.game_over:
            self._on_game_over()
            return

        player = self._gs.current_player
        log.debug("Beginning attack turn for P%d", player)
        self._refresh_attack_boards()

        if self._autoplay:
            self._set_status(CT.STATUS_AI_TURN, player)
            engine = self._autoplay_engines[player]
            self.after(CG.AUTOPLAY_MOVE_DELAY_MS,
                       lambda: self._schedule_ai_attack(
                           player, engine, self._game_id))
        elif player == self._human_player:
            self._set_status(CT.STATUS_HUMAN_TURN, player)
        else:
            self._set_status(CT.STATUS_AI_TURN, player)
            self.after(CG.AI_THINK_DELAY_MS,
                       lambda: self._schedule_ai_attack(
                           player, self._ai_engine, self._game_id))

    def _on_human_attack_click(self, row: int, col: int) -> None:
        if self._gs is None or self._gs.game_over:
            return
        if self._gs.current_player != self._human_player:
            return
        if self._gs.attack_boards[self._human_player][row][col] != UNKNOWN:
            messagebox.showinfo(CT.WINDOW_TITLE, CT.MSG_CELL_ALREADY_FIRED)
            return
        self._commit_attack(self._human_player, row, col)

    # ------------------------------------------------------------------
    # Attack phase -- AI thread
    # ------------------------------------------------------------------

    def _schedule_ai_attack(self, player: int, engine,
                             game_id: int) -> None:
        if game_id != self._game_id:
            return
        if self._gs is None or self._gs.game_over:
            return

        attack_copy = [row[:] for row in self._gs.attack_boards[player]]
        num_r       = self._gs.num_rows
        num_c       = self._gs.num_cols
        opponent    = OTHER_PLAYER[player]
        remaining_shapes = [s.shape for s in self._gs.ships[opponent]
                            if not s.is_sunk]
        sunk_ships  = list(self._gs.sunk_ships(opponent))

        def _run():
            r, c = engine.next_attack(
                attack_copy, num_r, num_c, remaining_shapes, sunk_ships
            )
            self.after(0, lambda: self._on_ai_attack_result(
                r, c, player, game_id))

        threading.Thread(target=_run, daemon=True,
                         name="AI-attack-P" + str(player)).start()

    def _on_ai_attack_result(self, row: int, col: int,
                               player: int, game_id: int) -> None:
        if game_id != self._game_id:
            log.debug("Stale AI attack result discarded")
            return
        if self._gs is None or self._gs.game_over:
            return
        if self._gs.current_player != player:
            log.debug("Stale AI attack result (player mismatch) discarded")
            return
        self._commit_attack(player, row, col)

    # ------------------------------------------------------------------
    # Commit attack (shared between human and AI)
    # ------------------------------------------------------------------

    def _commit_attack(self, attacker: int, row: int, col: int) -> None:
        if self._gs is None:
            return
        try:
            result = self._gs.attack(attacker, row, col)
        except ValueError as exc:
            log.warning("Invalid attack (%d,%d) by P%d: %s", row, col, attacker, exc)
            return

        self._stats.record_shot(attacker, result, self._gs)
        self._set_status(CT.STATUS_ANIMATING)
        self._animate_attack_result(attacker, result)

    def _animate_attack_result(self, attacker: int, result) -> None:
        if self._battleship_board is None:
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._after_attack)
            return
        s    = UI
        vp   = self._view_player
        r, c = result.row, result.col

        if result.sunk_ship is not None:
            # Sunk: flash all sunk ship cells on attacker's attack board
            sunk_cells = list(result.sunk_ship.cells)
            if attacker == vp:
                # Attacker IS the view player: show sunk cells in their attack board
                def _after_sunk():
                    self._battleship_board.mark_sunk_on_attack(sunk_cells)
                    self._after_attack()
                for cell_r, cell_c in sunk_cells:
                    self._battleship_board.attack_grid.flash_cell(
                        cell_r, cell_c,
                        s.SUNK_FLASH_COLOR, s.HIT_COLOR,
                        CG.SUNK_FLASH_COUNT, CG.SUNK_FLASH_INTERVAL_MS,
                    )
                self.after(
                    CG.SUNK_FLASH_COUNT * CG.SUNK_FLASH_INTERVAL_MS
                    + CG.AI_INTER_MOVE_PAUSE_MS + CG.RESULT_HOLD_MS,
                    _after_sunk,
                )
            else:
                # Attacker is the OPPONENT; show sunk cells on fleet grid
                def _after_sunk():
                    self._render_fleet_grid(vp)
                    self._after_attack()
                for cell_r, cell_c in sunk_cells:
                    self._battleship_board.fleet_grid.flash_cell(
                        cell_r, cell_c,
                        s.SUNK_FLASH_COLOR, s.HIT_COLOR,
                        CG.SUNK_FLASH_COUNT, CG.SUNK_FLASH_INTERVAL_MS,
                    )
                self.after(
                    CG.SUNK_FLASH_COUNT * CG.SUNK_FLASH_INTERVAL_MS
                    + CG.AI_INTER_MOVE_PAUSE_MS + CG.RESULT_HOLD_MS,
                    _after_sunk,
                )
            msg = CT.MSG_SUNK.format(name=result.sunk_ship.name)
            self._set_status(msg)
        elif result.hit:
            flash_color = s.HIT_FLASH_COLOR
            final_color = s.HIT_COLOR
            if attacker == vp:
                self._battleship_board.attack_grid.flash_cell(
                    r, c, flash_color, final_color,
                    CG.HIT_FLASH_COUNT, CG.HIT_FLASH_INTERVAL_MS,
                )
            else:
                self._battleship_board.fleet_grid.flash_cell(
                    r, c, flash_color, final_color,
                    CG.HIT_FLASH_COUNT, CG.HIT_FLASH_INTERVAL_MS,
                )
            self._set_status(CT.MSG_HIT)
            self.after(
                CG.HIT_FLASH_COUNT * CG.HIT_FLASH_INTERVAL_MS
                + CG.AI_INTER_MOVE_PAUSE_MS + CG.RESULT_HOLD_MS,
                self._after_attack,
            )
        else:
            flash_color = s.MISS_FLASH_COLOR
            final_color = s.MISS_COLOR
            if attacker == vp:
                self._battleship_board.attack_grid.flash_cell(
                    r, c, flash_color, final_color,
                    CG.MISS_FLASH_COUNT, CG.MISS_FLASH_INTERVAL_MS,
                )
            else:
                self._battleship_board.fleet_grid.flash_cell(
                    r, c, s.FLEET_WATER_COLOR, s.FLEET_WATER_COLOR,
                    CG.MISS_FLASH_COUNT, CG.MISS_FLASH_INTERVAL_MS,
                )
            self._set_status(CT.MSG_MISS)
            self.after(
                CG.MISS_FLASH_COUNT * CG.MISS_FLASH_INTERVAL_MS
                + CG.AI_INTER_MOVE_PAUSE_MS + CG.RESULT_HOLD_MS,
                self._after_attack,
            )

    def _after_attack(self) -> None:
        if self._gs is None:
            return
        if self._gs.game_over:
            self._on_game_over()
        else:
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._begin_attack_turn)

    # ------------------------------------------------------------------
    # Game over
    # ------------------------------------------------------------------

    def _on_game_over(self) -> None:
        if self._gs is None or self._stats is None:
            return
        winner = self._gs.winner
        self._stats.finalise(winner, self._human_player)
        self._refresh_attack_boards()

        if winner == PLAYER_1:
            msg = (CT.GAMEOVER_HUMAN_WINS if self._human_player == PLAYER_1
                   else CT.GAMEOVER_P1_WINS)
        elif winner == PLAYER_2:
            if self._human_player == PLAYER_2:
                msg = CT.GAMEOVER_HUMAN_WINS
            elif self._human_player == PLAYER_1:
                msg = CT.GAMEOVER_AI_WINS
            else:
                msg = CT.GAMEOVER_P2_WINS
        else:
            msg = CT.GAMEOVER_DRAW

        self._set_status(msg, winner)

        if self._battleship_board and winner is not None:
            s = UI
            color = (s.WIN_FLASH_COLOR_P1 if winner == PLAYER_1
                     else s.WIN_FLASH_COLOR_P2)
            for r in range(self._gs.num_rows):
                for c in range(self._gs.num_cols):
                    self._battleship_board.fleet_grid.flash_cell(
                        r, c, color, s.FLEET_WATER_COLOR,
                        CG.WIN_FLASH_COUNT, CG.WIN_FLASH_INTERVAL_MS,
                    )

        self.after(UI.STATS_DELAY_MS, self._show_stats)

    def _on_loaded_game_over(self) -> None:
        if self._gs is None:
            return
        if self._gs.phase == PHASE_DONE:
            self._setup_attack_phase()
            self._on_game_over()

    def _show_stats(self) -> None:
        if self._stats is None:
            return
        StatsWindow(self, self._stats, self._human_player)

    # ------------------------------------------------------------------
    # Menu / button handlers
    # ------------------------------------------------------------------

    def _on_new_game(self) -> None:
        log.debug("New game requested")
        self._game_id += 1
        self._show_start()

    def _on_save_game(self) -> None:
        if self._gs is None:
            messagebox.showinfo(CT.WINDOW_TITLE, CT.MSG_NO_GAME)
            return
        path = filedialog.asksaveasfilename(
            title=CT.MENU_SAVE,
            defaultextension=".json",
            filetypes=[(CT.SAVE_FILETYPE, "*.json")],
        )
        if not path:
            return
        try:
            save_game(self._gs, self._human_player, path)
            messagebox.showinfo(CT.WINDOW_TITLE, CT.MSG_SAVED.format(path=path))
        except Exception as exc:
            messagebox.showerror(CT.WINDOW_TITLE, CT.MSG_SAVE_ERROR.format(err=exc))

    def _on_load_game(self) -> None:
        path = filedialog.askopenfilename(
            title=CT.MENU_LOAD,
            filetypes=[(CT.SAVE_FILETYPE, "*.json")],
        )
        if not path:
            return
        try:
            state, human_player = load_game(path)
        except Exception as exc:
            messagebox.showerror(CT.WINDOW_TITLE, CT.MSG_LOAD_ERROR.format(err=exc))
            return
        self._autoplay  = (human_player is None)
        self._game_id  += 1
        self._show_game(state, human_player)

    def _on_start_normal(self, num_rows: int, num_cols: int,
                          fleet_preset: str, first_player: str) -> None:
        self._autoplay = False
        self._on_start_new_game(num_rows, num_cols, fleet_preset, first_player)

    def _on_start_autoplay(self, num_rows: int, num_cols: int,
                            fleet_preset: str) -> None:
        self._autoplay = True
        self._on_start_new_game(num_rows, num_cols, fleet_preset, _FIRST_HUMAN)

    def _on_start_new_game(self, num_rows: int, num_cols: int,
                            fleet_preset: str, first_player: str) -> None:
        log.debug("New game: %dx%d fleet=%s first=%s autoplay=%s",
                  num_cols, num_rows, fleet_preset, first_player, self._autoplay)

        fleet_spec   = CG.FLEET_PRESETS.get(fleet_preset,
                           CG.FLEET_PRESETS[CG.FLEET_PRESET_DEFAULT])

        if self._autoplay:
            human_player = None
            first_attacker = PLAYER_1
        elif first_player == _FIRST_HUMAN:
            human_player   = PLAYER_1
            first_attacker = PLAYER_1
        else:
            human_player   = PLAYER_1
            first_attacker = PLAYER_2

        state = GameState(
            first_attacker = first_attacker,
            num_rows       = num_rows,
            num_cols       = num_cols,
            fleet_spec     = fleet_spec,
        )
        self._show_game(state, human_player)

    # ------------------------------------------------------------------
    # Help dialogs
    # ------------------------------------------------------------------

    def _show_rules(self) -> None:
        s   = UI
        dlg = tk.Toplevel(self)
        dlg.title(CT.MENU_RULES)
        dlg.configure(bg=s.BG_COLOR)
        dlg.resizable(False, False)
        dlg.grab_set()
        tk.Label(dlg, text=CT.RULES_TEXT,
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR, bg=s.BG_COLOR,
                 wraplength=s.RULES_WRAP_WIDTH, justify="left",
                 padx=s.RULES_LABEL_PADX, pady=s.RULES_LABEL_PADY).pack()
        tk.Button(dlg, text=CT.BTN_CLOSE,
                  font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
                  activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                  relief=s.BTN_RELIEF, bd=s.BTN_BD,
                  padx=s.BTN_PADX, pady=s.BTN_PADY,
                  command=dlg.destroy).pack(pady=(0, s.RULES_CLOSE_PADY_BOT))
        self._center_dialog(dlg)

    def _show_about(self) -> None:
        s   = UI
        dlg = tk.Toplevel(self)
        dlg.title(CT.ABOUT_TITLE)
        dlg.configure(bg=s.BG_COLOR)
        dlg.resizable(False, False)
        dlg.grab_set()
        tk.Label(dlg, text=CT.ABOUT_SUBTITLE,
                 font=s.START_TITLE_FONT, fg=s.START_TITLE_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.ABOUT_TITLE_PADY_TOP, 0),
                                     padx=s.ABOUT_PADX)
        tk.Frame(dlg, height=1, bg=s.PANEL_DIVIDER_COLOR).pack(
            fill="x", padx=s.ABOUT_PADX, pady=(8, 0))
        tk.Label(dlg, text=CT.ABOUT_BODY,
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR, bg=s.BG_COLOR,
                 wraplength=s.ABOUT_WRAP_WIDTH, justify="center",
                 padx=s.ABOUT_PADX, pady=s.ABOUT_PADY).pack()
        tk.Button(dlg, text=CT.BTN_CLOSE,
                  font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
                  activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                  relief=s.BTN_RELIEF, bd=s.BTN_BD,
                  padx=s.BTN_PADX, pady=s.BTN_PADY,
                  command=dlg.destroy).pack(pady=(0, s.ABOUT_CLOSE_PADY_BOT))
        self._center_dialog(dlg)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _set_status(self, text: str, player: "int | None" = None) -> None:
        if self._status_label is None:
            return
        if player == PLAYER_1:
            color = UI.TURN_COLOR_P1
        elif player == PLAYER_2:
            color = UI.TURN_COLOR_P2
        else:
            color = UI.STATUS_COLOR
        self._status_label.configure(text=text, fg=color)
        log.debug("Status: %r", text)

    def _fit_window(self) -> None:
        self.update_idletasks()
        w  = max(self.winfo_reqwidth(), self._min_width)
        h  = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = max(0, (sw - w) // 2)
        y  = max(0, (sh - h) // 2)
        self.geometry(str(w) + "x" + str(h) + "+" + str(x) + "+" + str(y))

    def _center_dialog(self, dlg: tk.Toplevel) -> None:
        dlg.update_idletasks()
        pw = self.winfo_width()
        ph = self.winfo_height()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        w  = dlg.winfo_reqwidth()
        h  = dlg.winfo_reqheight()
        x  = px + (pw - w) // 2
        y  = py + (ph - h) // 2
        dlg.geometry("+" + str(x) + "+" + str(y))
