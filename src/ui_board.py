"""
Battleship board widgets.

GridCanvas    -- a single labeled grid (fleet view OR attack view).
BattleshipBoard  -- side-by-side pair: own fleet grid + enemy attack grid.
PlacementPanel   -- full placement UI: grid + ship list + controls.
"""

import tkinter as tk
import tkinter.ttk as ttk
import logging

import config_ui   as UI
import config_text as CT
import config_game as CG
from game_logic import (
    WATER, UNKNOWN, MISS_MARK, HIT_MARK,
    PLAYER_1, PLAYER_2,
    ship_cells, can_place_ship, get_all_rotations,
)

log = logging.getLogger(__name__)


class GridCanvas(tk.Canvas):
    """
    A single Battleship grid with row/column labels.

    Coordinate layout (in pixels):
      Top-left corner of cell (row, col) =
        (LABEL_AREA_W + BOARD_PADDING + col*CELL_SIZE,
         LABEL_AREA_H + BOARD_PADDING + row*CELL_SIZE)
    """

    def __init__(self, parent, num_rows: int, num_cols: int, **kw):
        s = UI
        self._num_rows = num_rows
        self._num_cols = num_cols

        total_w = s.LABEL_AREA_W + s.BOARD_PADDING * 2 + num_cols * s.CELL_SIZE
        total_h = s.LABEL_AREA_H + s.BOARD_PADDING * 2 + num_rows * s.CELL_SIZE

        super().__init__(
            parent,
            width=total_w,
            height=total_h,
            bg=UI.BG_COLOR,
            highlightthickness=s.BORDER_WIDTH,
            highlightbackground=s.GRID_BORDER_COLOR,
            **kw,
        )
        self._cell_items  = {}   # (row,col) -> canvas item id
        self._ghost_items = []   # temporary ghost-placement items
        self._mark_items  = {}   # (row,col) -> canvas text item id for miss marks
        self._draw_labels()
        self._draw_cells(UNKNOWN)

    # ------------------------------------------------------------------
    # Internal drawing
    # ------------------------------------------------------------------

    def _cell_bbox(self, row: int, col: int):
        """Return (x1, y1, x2, y2) pixel bbox for a cell."""
        s  = UI
        ox = s.LABEL_AREA_W + s.BOARD_PADDING
        oy = s.LABEL_AREA_H + s.BOARD_PADDING
        x1 = ox + col * s.CELL_SIZE
        y1 = oy + row * s.CELL_SIZE
        x2 = x1 + s.CELL_SIZE
        y2 = y1 + s.CELL_SIZE
        return x1, y1, x2, y2

    def _draw_labels(self) -> None:
        s   = UI
        ox  = s.LABEL_AREA_W + s.BOARD_PADDING
        oy  = s.LABEL_AREA_H + s.BOARD_PADDING
        col_chars = CT.GRID_COL_LABELS

        for c in range(self._num_cols):
            cx = ox + c * s.CELL_SIZE + s.CELL_SIZE // 2
            cy = s.LABEL_AREA_H // 2
            self.create_text(cx, cy,
                             text=col_chars[c] if c < len(col_chars) else str(c),
                             font=s.LABEL_FONT,
                             fill=s.LABEL_COLOR)

        for r in range(self._num_rows):
            cx = s.LABEL_AREA_W // 2
            cy = oy + r * s.CELL_SIZE + s.CELL_SIZE // 2
            self.create_text(cx, cy,
                             text=str(r + 1),
                             font=s.LABEL_FONT,
                             fill=s.LABEL_COLOR)

    def _draw_cells(self, default_value: int) -> None:
        s = UI
        for r in range(self._num_rows):
            for c in range(self._num_cols):
                x1, y1, x2, y2 = self._cell_bbox(r, c)
                color = _cell_color(default_value, fleet_mode=False)
                item  = self.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=s.CELL_OUTLINE_COLOR,
                )
                self._cell_items[(r, c)] = item

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def set_cell_color(self, row: int, col: int, color: str) -> None:
        item = self._cell_items.get((row, col))
        if item:
            self.itemconfig(item, fill=color)

    def set_cell_mark(self, row: int, col: int, text: str, color: str) -> None:
        """Draw a text mark centred in a cell (e.g. 'x' for opponent miss)."""
        if (row, col) in self._mark_items:
            self.delete(self._mark_items[(row, col)])
        x1, y1, x2, y2 = self._cell_bbox(row, col)
        item = self.create_text(
            (x1 + x2) // 2, (y1 + y2) // 2,
            text=text, fill=color, font=UI.FLEET_MISS_MARK_FONT,
        )
        self._mark_items[(row, col)] = item

    def clear_all_marks(self) -> None:
        """Remove all text marks drawn by set_cell_mark."""
        for item in self._mark_items.values():
            self.delete(item)
        self._mark_items.clear()

    def flash_cell(self, row: int, col: int, flash_color: str,
                   original_color: str, count: int, interval_ms: int) -> None:
        """Flash a cell count times at interval_ms each half-cycle."""
        item = self._cell_items.get((row, col))
        if not item or count <= 0:
            self.set_cell_color(row, col, original_color)
            return
        self.itemconfig(item, fill=flash_color)
        self.after(
            interval_ms,
            lambda: self.flash_cell(row, col, original_color, flash_color,
                                    count - 1, interval_ms)
        )

    def set_fleet_board(self, fleet_board) -> None:
        """Render own fleet board (ships visible)."""
        s = UI
        for r in range(self._num_rows):
            for c in range(self._num_cols):
                val = fleet_board[r][c]
                color = s.SHIP_COLOR if val != WATER else s.FLEET_WATER_COLOR
                self.set_cell_color(r, c, color)

    def set_attack_board(self, attack_board) -> None:
        """Render attack board (opponent's waters)."""
        s = UI
        for r in range(self._num_rows):
            for c in range(self._num_cols):
                val = attack_board[r][c]
                if val == HIT_MARK:
                    color = s.HIT_COLOR
                elif val == MISS_MARK:
                    color = s.MISS_COLOR
                else:
                    color = s.ATTACK_UNKNOWN_COLOR
                self.set_cell_color(r, c, color)

    def mark_sunk_cells(self, cells) -> None:
        s = UI
        for r, c in cells:
            self.set_cell_color(r, c, s.SUNK_COLOR)

    def show_ghost(self, cells, valid: bool) -> None:
        """Show a translucent ghost for ship placement preview."""
        self.clear_ghost()
        s     = UI
        color = s.GHOST_VALID_COLOR if valid else s.GHOST_INVALID_COLOR
        for r, c in (cells or []):
            if 0 <= r < self._num_rows and 0 <= c < self._num_cols:
                x1, y1, x2, y2 = self._cell_bbox(r, c)
                item = self.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline=s.CELL_OUTLINE_COLOR,
                )
                self._ghost_items.append(item)

    def clear_ghost(self) -> None:
        for item in self._ghost_items:
            self.delete(item)
        self._ghost_items.clear()

    def pixel_to_cell(self, x: int, y: int):
        """Return (row, col) for pixel (x, y), or None if out of grid."""
        s  = UI
        ox = s.LABEL_AREA_W + s.BOARD_PADDING
        oy = s.LABEL_AREA_H + s.BOARD_PADDING
        col = (x - ox) // s.CELL_SIZE
        row = (y - oy) // s.CELL_SIZE
        if 0 <= row < self._num_rows and 0 <= col < self._num_cols:
            return row, col
        return None


# ------------------------------------------------------------------
# LiveStatsPanel
# ------------------------------------------------------------------

class LiveStatsPanel(tk.Frame):
    """
    Compact two-column stats table shown beside the grids during the attack phase.

    Columns : one per player (attacker's perspective).
    Fixed rows : Shots, Accuracy, Progress.
    Dynamic rows: one per unique ship type in the fleet showing N_sunk/N_total.
    """

    def __init__(self, parent, fleet_spec: list, p1_name: str, p2_name: str):
        s = UI
        super().__init__(parent, bg=s.SHIP_TABLE_HEADING_BG, relief="solid", bd=1)

        # Compute unique ship types and total count per type (same fleet for both players)
        seen = []
        self._type_totals = {}
        for spec in fleet_spec:
            nm = spec["name"]
            self._type_totals[nm] = self._type_totals.get(nm, 0) + spec["count"]
            if nm not in seen:
                seen.append(nm)
        self._ship_types = seen

        px = s.LIVE_STATS_PANEL_PADX
        py = s.LIVE_STATS_PANEL_PADY

        hbg = s.SHIP_TABLE_HEADING_BG
        hfg = s.SHIP_TABLE_HEADING_FG
        font_h = s.SHIP_LIST_FONT
        font_v = s.STATUS_FONT

        # Header row (row 0): empty label | p1_name | p2_name
        tk.Label(self, text=CT.LIVE_STATS_TITLE,
                 bg=hbg, fg=hfg, font=font_h, anchor="center",
                 ).grid(row=0, column=0, sticky="ew", padx=px, pady=py)
        tk.Label(self, text=p1_name,
                 bg=hbg, fg=hfg, font=font_h, anchor="center",
                 ).grid(row=0, column=1, sticky="ew", padx=px, pady=py)
        tk.Label(self, text=p2_name,
                 bg=hbg, fg=hfg, font=font_h, anchor="center",
                 ).grid(row=0, column=2, sticky="ew", padx=px, pady=py)

        # Data rows -- fixed metrics
        # Group 1: raw counts (Shots, Hits)
        # Group 2: derived ratios (Progress, Accuracy) -- separated by a thin divider
        self._vars = {}   # key -> (StringVar_p1, StringVar_p2)
        row_idx = 1
        for key, label in (
            ("shots",    CT.LIVE_STATS_ROW_SHOTS),
            ("hits",     CT.LIVE_STATS_ROW_HITS),
        ):
            self._add_row(row_idx, key, label, font_h, font_v, px, py)
            row_idx += 1

        # Progress and Accuracy are separated from the raw counts above and from the
        # ship-type rows below by explicit extra top-padding on the first row of each group.
        sep = s.LIVE_STATS_PANEL_SEP_H
        self._add_row(row_idx, "progress", CT.LIVE_STATS_ROW_PROG,
                      font_h, font_v, px, py, extra_top=sep)
        row_idx += 1
        self._add_row(row_idx, "accuracy", CT.LIVE_STATS_ROW_ACC,
                      font_h, font_v, px, py)
        row_idx += 1

        # Ship-type rows -- first one gets extra top padding to detach from the group above
        first_ship = True

        # One row per ship type
        for nm in self._ship_types:
            top = sep if first_ship else 0
            self._add_row(row_idx, "sunk_" + nm, nm, font_h, font_v, px, py,
                          extra_top=top)
            first_ship = False
            row_idx += 1

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

    def _add_row(self, row_idx: int, key: str, label: str,
                 font_h, font_v, padx: int, pady: int,
                 extra_top: int = 0) -> None:
        s = UI
        bg = (s.SHIP_TABLE_ROW_ACTIVE_BG if row_idx % 2 == 1
              else s.SHIP_TABLE_ROW_DONE_BG)
        fg_label = s.SHIP_TABLE_ROW_ACTIVE_FG if row_idx % 2 == 1 else s.SHIP_TABLE_ROW_DONE_FG
        fg_val   = s.TEXT_SECONDARY
        row_pady = (pady + extra_top, pady)
        tk.Label(self, text=label, bg=bg, fg=fg_label, font=font_h,
                 anchor="w",
                 ).grid(row=row_idx, column=0, sticky="ew", padx=padx, pady=row_pady)
        var1 = tk.StringVar(value="-")
        var2 = tk.StringVar(value="-")
        tk.Label(self, textvariable=var1, bg=bg, fg=fg_val, font=font_v,
                 anchor="center",
                 ).grid(row=row_idx, column=1, sticky="ew", padx=padx, pady=row_pady)
        tk.Label(self, textvariable=var2, bg=bg, fg=fg_val, font=font_v,
                 anchor="center",
                 ).grid(row=row_idx, column=2, sticky="ew", padx=padx, pady=row_pady)
        self._vars[key] = (var1, var2)

    def _set(self, key: str, v1: str, v2: str) -> None:
        if key in self._vars:
            self._vars[key][0].set(v1)
            self._vars[key][1].set(v2)

    def refresh(self, gs, stats) -> None:
        """Update all cells from the current GameState and GameStats."""
        s1 = stats.shots(PLAYER_1)
        s2 = stats.shots(PLAYER_2)
        self._set("shots", str(s1), str(s2))

        h1 = stats.hits(PLAYER_1)
        h2 = stats.hits(PLAYER_2)
        self._set("hits", str(h1), str(h2))

        a1 = stats.accuracy(PLAYER_1)
        a2 = stats.accuracy(PLAYER_2)
        self._set("accuracy",
                  "{:.1f}%".format(a1 * 100),
                  "{:.1f}%".format(a2 * 100))

        t1 = gs.total_ship_cells(PLAYER_2)   # cells P1 must hit
        t2 = gs.total_ship_cells(PLAYER_1)   # cells P2 must hit
        p1 = "{:.1f}%".format(h1 / t1 * 100) if t1 else "-"
        p2 = "{:.1f}%".format(h2 / t2 * 100) if t2 else "-"

        self._set("progress", p1, p2)

        # Per-type sunk counts
        # P1 column: ships of that type P1 sank from P2's fleet
        # P2 column: ships of that type P2 sank from P1's fleet
        sunk_by_p1 = {}
        for ship in gs.sunk_ships(PLAYER_2):
            sunk_by_p1[ship.name] = sunk_by_p1.get(ship.name, 0) + 1
        sunk_by_p2 = {}
        for ship in gs.sunk_ships(PLAYER_1):
            sunk_by_p2[ship.name] = sunk_by_p2.get(ship.name, 0) + 1

        for nm in self._ship_types:
            total = self._type_totals[nm]
            v1 = str(sunk_by_p1.get(nm, 0)) + "/" + str(total)
            v2 = str(sunk_by_p2.get(nm, 0)) + "/" + str(total)
            self._set("sunk_" + nm, v1, v2)


# ------------------------------------------------------------------
# BattleshipBoard
# ------------------------------------------------------------------

class BattleshipBoard(tk.Frame):
    """
    Two side-by-side grids for the attack phase, with an optional live stats panel.

      left   -- own fleet grid (ships visible, receives hits highlighted)
      middle/right -- LiveStatsPanel (if fleet_spec provided)
      right  -- enemy waters grid (attack markers, clickable by human)

    stats_position: "middle" inserts the panel between the two grids;
                    "right"  places it after the attack grid.
    """

    def __init__(self, parent, num_rows: int, num_cols: int,
                 left_label: str, right_label: str,
                 fleet_spec=None, p1_name: str = "", p2_name: str = "",
                 stats_position: str = "middle",
                 on_attack_click=None):
        super().__init__(parent, bg=UI.BG_COLOR)
        self._on_attack_click = on_attack_click
        self._num_rows = num_rows
        self._num_cols = num_cols

        s = UI

        has_panel = fleet_spec is not None
        if has_panel and stats_position == "middle":
            fleet_col  = 0
            stats_col  = 1
            attack_col = 2
        elif has_panel:   # "right"
            fleet_col  = 0
            attack_col = 1
            stats_col  = 2
        else:
            fleet_col  = 0
            attack_col = 1
            stats_col  = None

        half_gap = s.GRID_INTER_PAD // 2

        # Left grid (own fleet)
        left_frame = tk.Frame(self, bg=s.BG_COLOR)
        left_frame.grid(row=0, column=fleet_col, padx=(0, half_gap))
        tk.Label(left_frame, text=left_label, font=s.HEADER_FONT,
                 fg=s.TEXT_COLOR, bg=s.BG_COLOR).pack()
        self.fleet_grid = GridCanvas(left_frame, num_rows, num_cols)
        self.fleet_grid.pack()

        # Right grid (attack board)
        right_frame = tk.Frame(self, bg=s.BG_COLOR)
        right_frame.grid(row=0, column=attack_col, padx=(half_gap, 0))
        tk.Label(right_frame, text=right_label, font=s.HEADER_FONT,
                 fg=s.TEXT_COLOR, bg=s.BG_COLOR).pack()
        self.attack_grid = GridCanvas(right_frame, num_rows, num_cols)
        self.attack_grid.pack()

        # Live stats panel (optional)
        self._live_stats = None
        if has_panel:
            self._live_stats = LiveStatsPanel(self, fleet_spec, p1_name, p2_name)
            self._live_stats.grid(row=0, column=stats_col,
                                  padx=half_gap, sticky="ns")

        if on_attack_click:
            self.attack_grid.bind("<Button-1>", self._on_click)

    def _on_click(self, event) -> None:
        cell = self.attack_grid.pixel_to_cell(event.x, event.y)
        if cell and self._on_attack_click:
            self._on_attack_click(*cell)

    def update_fleet_board(self, fleet_board) -> None:
        self.fleet_grid.set_fleet_board(fleet_board)

    def update_attack_board(self, attack_board) -> None:
        self.attack_grid.set_attack_board(attack_board)

    def flash_attack_cell(self, row, col, flash_color, final_color,
                          count, interval_ms) -> None:
        self.attack_grid.flash_cell(row, col, flash_color, final_color,
                                    count, interval_ms)

    def flash_fleet_cell(self, row, col, flash_color, final_color,
                         count, interval_ms) -> None:
        self.fleet_grid.flash_cell(row, col, flash_color, final_color,
                                   count, interval_ms)

    def mark_sunk_on_attack(self, cells) -> None:
        self.attack_grid.mark_sunk_cells(cells)

    def mark_sunk_on_fleet(self, cells) -> None:
        self.fleet_grid.mark_sunk_cells(cells)

    def update_live_stats(self, gs, stats) -> None:
        if self._live_stats:
            self._live_stats.refresh(gs, stats)


# ------------------------------------------------------------------
# PlacementPanel
# ------------------------------------------------------------------

class PlacementPanel(tk.Frame):
    """
    Ship placement UI for one player.
    Shows the fleet grid, a list of ships to place, orientation toggle,
    random-placement button, and confirm-fleet button.

    Callbacks (all optional):
      on_confirm()         -- called when Confirm Fleet is clicked
      on_random()          -- called when Random Place is clicked
      on_ship_select(idx)  -- called when the user selects a ship in the list
    """

    def __init__(self, parent, num_rows: int, num_cols: int, flat_fleet: list,
                 on_confirm=None, on_random=None, on_ship_select=None,
                 on_undo=None, on_clear=None):
        super().__init__(parent, bg=UI.BG_COLOR)
        self._num_rows       = num_rows
        self._num_cols       = num_cols
        self._original_fleet = list(flat_fleet)
        self._flat_fleet     = list(flat_fleet)
        self._on_confirm     = on_confirm
        self._on_random      = on_random
        self._on_ship_select = on_ship_select
        self._on_undo        = on_undo
        self._on_clear       = on_clear

        self._rotation_idx = 0
        self._rotations    = []
        self._selected_idx = 0

        self._build()
        self._update_rotations()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        s = UI

        # --- Grid (left side) ----------------------------------------
        grid_frame = tk.Frame(self, bg=s.BG_COLOR)
        grid_frame.pack(side="left", padx=(0, s.GRID_INTER_PAD // 2))

        self.grid_canvas = GridCanvas(grid_frame, self._num_rows, self._num_cols)
        self.grid_canvas.pack()
        # Reset all cells to fleet-water color
        for r in range(self._num_rows):
            for c in range(self._num_cols):
                self.grid_canvas.set_cell_color(r, c, s.FLEET_WATER_COLOR)

        # Mouse bindings on the placement grid
        self.grid_canvas.bind("<Button-1>", self._on_grid_click)
        self.grid_canvas.bind("<Motion>",   self._on_grid_motion)
        self.grid_canvas.bind("<Leave>",    self._on_grid_leave)

        # --- Right panel (ship list + buttons) -----------------------
        right = tk.Frame(self, bg=s.BG_COLOR)
        right.pack(side="left", fill="y")

        tk.Label(right, text=CT.PLACEMENT_DEPLOY_HEADER,
                 font=s.HEADER_FONT, fg=s.TEXT_COLOR, bg=s.BG_COLOR).pack(anchor="w")

        # Ship deployment table (Treeview with 3 columns)
        # Layout: scrollbar sits at the right of table_frame; header + treeview
        # share table_inner so the header width == the treeview width exactly.
        table_frame = tk.Frame(right, bg=s.BG_COLOR)
        table_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(table_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        table_inner = tk.Frame(table_frame, bg=s.BG_COLOR)
        table_inner.pack(side="left", fill="both", expand=True)

        # Custom header row -- plain tk.Labels so skin colors are always honoured.
        # grid() with minsize lets each column header align with the treeview column.
        header_frame = tk.Frame(table_inner, bg=s.SHIP_TABLE_HEADING_BG)
        header_frame.pack(fill="x")
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, minsize=s.SHIP_TABLE_COL_COUNT_W)
        header_frame.columnconfigure(2, minsize=s.SHIP_TABLE_COL_COUNT_W)
        tk.Label(
            header_frame, text=CT.PLACEMENT_COL_TYPE,
            bg=s.SHIP_TABLE_HEADING_BG, fg=s.SHIP_TABLE_HEADING_FG,
            font=s.SHIP_LIST_FONT, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=(4, 0), pady=2)
        tk.Label(
            header_frame, text=CT.PLACEMENT_COL_DEPLOYED,
            bg=s.SHIP_TABLE_HEADING_BG, fg=s.SHIP_TABLE_HEADING_FG,
            font=s.SHIP_LIST_FONT, anchor="center",
        ).grid(row=0, column=1, sticky="ew", pady=2)
        tk.Label(
            header_frame, text=CT.PLACEMENT_COL_LEFT,
            bg=s.SHIP_TABLE_HEADING_BG, fg=s.SHIP_TABLE_HEADING_FG,
            font=s.SHIP_LIST_FONT, anchor="center",
        ).grid(row=0, column=2, sticky="ew", pady=2)

        style_name = "BattleshipDeploy.Treeview"
        _tv_style = ttk.Style()
        _tv_style.configure(
            style_name,
            background=s.SHIP_TABLE_ROW_DONE_BG,
            foreground=s.SHIP_TABLE_ROW_DONE_FG,
            fieldbackground=s.SHIP_TABLE_ROW_DONE_BG,
            font=s.SHIP_LIST_FONT,
            rowheight=24,
        )
        _tv_style.map(
            style_name,
            background=[("selected", s.SHIP_TABLE_SELECT_BG)],
            foreground=[("selected", s.SHIP_TABLE_SELECT_FG)],
        )

        self._tree = ttk.Treeview(
            table_inner,
            style=style_name,
            columns=("type", "deployed", "left"),
            show="",
            height=s.SHIP_TABLE_VISIBLE_ROWS,
            selectmode="browse",
        )
        self._tree.column("type",     width=s.SHIP_TABLE_COL_TYPE_W,  stretch=True,  anchor="w")
        self._tree.column("deployed", width=s.SHIP_TABLE_COL_COUNT_W, stretch=False, anchor="center")
        self._tree.column("left",     width=s.SHIP_TABLE_COL_COUNT_W, stretch=False, anchor="center")
        self._tree.tag_configure(
            "active",
            background=s.SHIP_TABLE_ROW_ACTIVE_BG,
            foreground=s.SHIP_TABLE_ROW_ACTIVE_FG,
        )
        self._tree.tag_configure(
            "done",
            background=s.SHIP_TABLE_ROW_DONE_BG,
            foreground=s.SHIP_TABLE_ROW_DONE_FG,
        )

        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self._tree.yview)
        self._tree.pack(fill="both", expand=True)

        self._tree_iids = {}   # name -> iid
        self._table_types = [] # [(name, size), ...] in original order
        self._init_table()
        self._tree.bind("<<TreeviewSelect>>", self._on_table_select)

        # Orientation/rotation label
        self._orient_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self._orient_var,
                 font=s.STATUS_FONT, fg=s.TEXT_SECONDARY, bg=s.BG_COLOR).pack(pady=(4, 0))

        # Rotate button
        tk.Button(
            right, text=CT.BTN_ROTATE,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            command=self.rotate_ship,
        ).pack(fill="x", pady=(2, 0))

        # Random place button
        tk.Button(
            right, text=CT.BTN_RANDOM_PLACE,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            command=self._do_random,
        ).pack(fill="x", pady=(4, 0))

        # Undo last placement button
        self._undo_btn = tk.Button(
            right, text=CT.BTN_UNDO_PLACE,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            command=self._do_undo,
            state="disabled",
        )
        self._undo_btn.pack(fill="x", pady=(4, 0))

        # Confirm fleet button
        self._confirm_btn = tk.Button(
            right, text=CT.BTN_CONFIRM_FLEET,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            command=self._do_confirm,
            state="disabled",
        )
        self._confirm_btn.pack(fill="x", pady=(4, 0))

        # Clear all button
        self._clear_btn = tk.Button(
            right, text=CT.BTN_CLEAR_FLEET,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            command=self._do_clear,
            state="disabled",
        )
        self._clear_btn.pack(fill="x", pady=(2, 0))

        # Bind keyboard R for rotate
        self.bind_all("<r>", lambda e: self.rotate_ship())
        self.bind_all("<R>", lambda e: self.rotate_ship())

    # ------------------------------------------------------------------
    # List helpers
    # ------------------------------------------------------------------

    def _init_table(self) -> None:
        """Insert one row per unique ship type (preserving original fleet order)."""
        seen = set()
        for spec in self._original_fleet:
            name = spec["name"]
            size = len(spec["shape"])
            key  = (name, size)
            if key not in seen:
                seen.add(key)
                self._table_types.append(key)

        total_by_name = {}
        for spec in self._original_fleet:
            total_by_name[spec["name"]] = total_by_name.get(spec["name"], 0) + 1

        for name, size in self._table_types:
            total = total_by_name[name]
            label = name + " (" + str(size) + " cells)"
            iid   = self._tree.insert("", "end",
                                      values=(label, 0, total),
                                      tags=("active",))
            self._tree_iids[name] = iid

        if self._tree_iids:
            first_iid = self._tree_iids[self._table_types[0][0]]
            self._tree.selection_set(first_iid)

    def _refresh_table(self) -> None:
        """Update Deployed/Left counters and row tags in place."""
        remaining_by_name = {}
        for spec in self._flat_fleet:
            remaining_by_name[spec["name"]] = remaining_by_name.get(spec["name"], 0) + 1

        total_by_name = {}
        for spec in self._original_fleet:
            total_by_name[spec["name"]] = total_by_name.get(spec["name"], 0) + 1

        for name, size in self._table_types:
            iid      = self._tree_iids[name]
            total    = total_by_name[name]
            left     = remaining_by_name.get(name, 0)
            deployed = total - left
            tag      = "active" if left > 0 else "done"
            label    = name + " (" + str(size) + " cells)"
            self._tree.item(iid, values=(label, deployed, left), tags=(tag,))

        # Select first row that still has ships left
        for name, _ in self._table_types:
            if remaining_by_name.get(name, 0) > 0:
                iid = self._tree_iids[name]
                self._tree.selection_set(iid)
                self._tree.see(iid)
                break

    def _on_table_select(self, event) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        iid = sel[0]
        name = next((n for n, i in self._tree_iids.items() if i == iid), None)
        if name is None:
            return
        # Find first pending ship with this name
        for i, spec in enumerate(self._flat_fleet):
            if spec["name"] == name:
                self._selected_idx = i
                self._update_rotations()
                if self._on_ship_select:
                    self._on_ship_select(self._selected_idx)
                return
        # Name has no ships left -- keep selection visual but don't change idx
        log.debug("Table row selected but no pending ships for %s", name)

    # ------------------------------------------------------------------
    # Mouse handlers
    # ------------------------------------------------------------------

    def _on_grid_motion(self, event) -> None:
        cell = self.grid_canvas.pixel_to_cell(event.x, event.y)
        if cell is None or not self._flat_fleet or not self.current_shape:
            self.grid_canvas.clear_ghost()
            return
        row, col = cell
        cells    = ship_cells(row, col, self.current_shape,
                              self._num_rows, self._num_cols)
        valid    = cells is not None
        self.grid_canvas.show_ghost(cells, valid)

    def _on_grid_leave(self, event) -> None:
        self.grid_canvas.clear_ghost()

    def _on_grid_click(self, event) -> None:
        if not self._flat_fleet or not self.current_shape:
            return
        cell = self.grid_canvas.pixel_to_cell(event.x, event.y)
        if cell is None:
            return
        row, col = cell
        if self._click_handler:
            self._click_handler(row, col, self.current_shape, self._selected_idx)

    # ------------------------------------------------------------------

    def set_click_handler(self, handler) -> None:
        """handler(row, col, shape, pending_idx) called on a grid click."""
        self._click_handler = handler

    _click_handler = None

    # ------------------------------------------------------------------
    # Public helpers called by the app
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Rotation helpers
    # ------------------------------------------------------------------

    def _update_rotations(self) -> None:
        """Recompute available rotations for the currently selected ship."""
        if self._flat_fleet:
            idx = min(self._selected_idx, len(self._flat_fleet) - 1)
            self._selected_idx = idx
            self._rotations    = get_all_rotations(self._flat_fleet[idx]["shape"])
            self._rotation_idx = 0
        else:
            self._rotations    = []
            self._rotation_idx = 0
        self._update_orient_label()

    def _update_orient_label(self) -> None:
        total = len(self._rotations)
        if total == 0:
            self._orient_var.set("")
            return
        idx = self._rotation_idx
        if total == 1:
            self._orient_var.set(CT.PLACEMENT_ORIENT_FIXED)
        elif total == 2:
            self._orient_var.set(
                CT.PLACEMENT_ORIENT_H if idx == 0 else CT.PLACEMENT_ORIENT_V
            )
        else:
            self._orient_var.set(
                CT.PLACEMENT_ORIENT_ROTATION.format(idx=idx + 1, total=total)
            )

    @property
    def current_shape(self):
        """Return the currently selected rotation of the next ship, or []."""
        if not self._rotations:
            return []
        return self._rotations[self._rotation_idx]

    def rotate_ship(self) -> None:
        """Advance to the next rotation of the current ship."""
        if not self._rotations:
            return
        self._rotation_idx = (self._rotation_idx + 1) % len(self._rotations)
        self.grid_canvas.clear_ghost()
        self._update_orient_label()
        log.debug("PlacementPanel: rotation idx=%d/%d",
                  self._rotation_idx, len(self._rotations))

    def toggle_orientation(self) -> None:
        """Alias for rotate_ship kept for backwards compatibility."""
        self.rotate_ship()

    @property
    def horizontal(self) -> bool:
        """Backwards-compat property: True when the current rotation is the canonical one."""
        return self._rotation_idx == 0

    def mark_ship_placed(self, cells) -> None:
        """Color placed ship cells on the grid and remove the selected ship from list."""
        s = UI
        for r, c in cells:
            self.grid_canvas.set_cell_color(r, c, s.SHIP_COLOR)
        if self._flat_fleet:
            idx = min(self._selected_idx, len(self._flat_fleet) - 1)
            self._flat_fleet.pop(idx)
        self._selected_idx = 0
        self._refresh_table()
        self._update_rotations()
        self._undo_btn.config(state="normal")
        self._clear_btn.config(state="normal")
        if not self._flat_fleet:
            self._confirm_btn.config(state="normal")

    def restore_ship(self, spec, cells) -> None:
        """Undo one placement: clear cells on canvas and return ship to pending list."""
        s = UI
        for r, c in cells:
            self.grid_canvas.set_cell_color(r, c, s.FLEET_WATER_COLOR)
        self._flat_fleet.insert(0, spec)
        self._selected_idx = 0
        self._refresh_table()
        self._update_rotations()
        self._confirm_btn.config(state="disabled")
        nothing_placed = len(self._flat_fleet) >= len(self._original_fleet)
        btn_state = "disabled" if nothing_placed else "normal"
        self._undo_btn.config(state=btn_state)
        self._clear_btn.config(state=btn_state)

    def restore_all(self) -> None:
        """Clear all placements: reset canvas and pending list to the original fleet."""
        s = UI
        for r in range(self._num_rows):
            for c in range(self._num_cols):
                self.grid_canvas.set_cell_color(r, c, s.FLEET_WATER_COLOR)
        self._flat_fleet   = list(self._original_fleet)
        self._selected_idx = 0
        self._refresh_table()
        self._update_rotations()
        self._confirm_btn.config(state="disabled")
        self._undo_btn.config(state="disabled")
        self._clear_btn.config(state="disabled")

    def set_fleet_board(self, fleet_board) -> None:
        """Refresh the entire grid from a fleet_board (e.g. after random place)."""
        self.grid_canvas.set_fleet_board(fleet_board)

    def all_placed(self) -> bool:
        return len(self._flat_fleet) == 0

    def _do_random(self) -> None:
        if self._on_random:
            self._on_random()

    def _do_undo(self) -> None:
        if self._on_undo:
            self._on_undo()

    def _do_clear(self) -> None:
        if self._on_clear:
            self._on_clear()

    def _do_confirm(self) -> None:
        if self._on_confirm:
            self._on_confirm()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _cell_color(value: int, fleet_mode: bool) -> str:
    s = UI
    if fleet_mode:
        return s.SHIP_COLOR if value != WATER else s.FLEET_WATER_COLOR
    if value == HIT_MARK:
        return s.HIT_COLOR
    if value == MISS_MARK:
        return s.MISS_COLOR
    return s.ATTACK_UNKNOWN_COLOR
