"""StatsWindow -- Battleship end-of-game summary dialog with optional chart."""

import tkinter as tk
import logging

import config_ui   as UI
import config_text as CT
from game_logic import PLAYER_1, PLAYER_2

log = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    _MPL_OK = True
except Exception:
    _MPL_OK = False
    log.debug("matplotlib unavailable -- stats chart disabled")


class StatsWindow(tk.Toplevel):
    """Modal stats window shown at end of game."""

    def __init__(self, parent, stats, human_player):
        super().__init__(parent)
        self._stats        = stats
        self._human_player = human_player
        self.title(CT.STATS_TITLE)
        self.resizable(False, False)
        self.configure(bg=UI.BG_COLOR)
        self.grab_set()
        self._build()
        self._center(parent)

    # ------------------------------------------------------------------

    def _build(self) -> None:
        s   = UI
        st  = self._stats
        pad = s.STATS_PADDING

        outer = tk.Frame(self, bg=s.BG_COLOR, padx=pad, pady=pad)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text=CT.STATS_TITLE,
            font=s.STATS_TITLE_FONT,
            fg=s.STATS_TITLE_COLOR,
            bg=s.BG_COLOR,
        ).pack(pady=(0, s.STATS_TITLE_PADY_BOT))

        # Result
        self._section(outer, CT.STATS_SECTION_RESULT)
        self._row(outer, CT.STATS_WINNER_LABEL, self._winner_text())

        # Shots
        self._section(outer, CT.STATS_SECTION_SHOTS)
        self._shots_table(outer)

        # Accuracy
        self._section(outer, CT.STATS_SECTION_ACCURACY)
        self._row(outer, CT.STATS_ROW_ACCURACY_P1,
                  _fmt_pct(st.accuracy(PLAYER_1)))
        self._row(outer, CT.STATS_ROW_ACCURACY_P2,
                  _fmt_pct(st.accuracy(PLAYER_2)))

        # Ships sunk
        self._section(outer, CT.STATS_SECTION_SHIPS)
        self._row(outer, CT.STATS_ROW_SHIPS_SUNK_P1, str(st.ships_sunk(PLAYER_1)))
        self._row(outer, CT.STATS_ROW_SHIPS_SUNK_P2, str(st.ships_sunk(PLAYER_2)))
        self._row(outer, CT.STATS_ROW_STREAK_P1, str(st.longest_streak(PLAYER_1)))
        self._row(outer, CT.STATS_ROW_STREAK_P2, str(st.longest_streak(PLAYER_2)))

        # Timing
        self._section(outer, CT.STATS_SECTION_TIMING)
        self._row(outer, CT.STATS_DURATION_LABEL, _fmt_dur(st.game_duration))

        # Advantage chart
        if s.STATS_SHOW_CHART and _MPL_OK:
            self._build_chart(outer)

        # Progress chart
        if s.STATS_SHOW_PROGRESS_CHART and _MPL_OK:
            self._build_progress_chart(outer)

        tk.Frame(outer, height=s.STATS_CLOSE_SPACER_H, bg=s.BG_COLOR).pack()
        tk.Button(
            outer,
            text=CT.BTN_CLOSE,
            font=s.BTN_FONT,
            fg=s.BTN_FG,
            bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG,
            activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF,
            bd=s.BTN_BD,
            padx=s.BTN_PADX,
            pady=s.BTN_PADY,
            command=self.destroy,
        ).pack(pady=(s.STATS_CLOSE_BTN_PADY_TOP, 0))

    # ------------------------------------------------------------------

    def _section(self, parent, text: str) -> None:
        s = UI
        tk.Label(
            parent,
            text=text,
            font=s.STATS_SECTION_FONT,
            fg=s.STATS_SECTION_FG,
            bg=s.STATS_SECTION_BG,
            anchor="w",
            padx=s.STATS_ROW_PADX,
            pady=s.STATS_SECTION_PADY,
        ).pack(fill="x",
               pady=(s.STATS_SECTION_PACK_PADY_TOP, s.STATS_SECTION_PACK_PADY_BOT))

    def _row(self, parent, label: str, value: str) -> None:
        s   = UI
        row = tk.Frame(parent, bg=s.BG_COLOR)
        row.pack(fill="x", padx=s.STATS_ROW_PADX, pady=s.STATS_ROW_PADY)
        tk.Label(row, text=label, font=s.STATS_ROW_LABEL_FONT,
                 fg=s.STATS_ROW_LABEL_COLOR, bg=s.BG_COLOR,
                 anchor="w").pack(side="left")
        tk.Label(row, text=value, font=s.STATS_ROW_VALUE_FONT,
                 fg=s.STATS_ROW_VALUE_COLOR, bg=s.BG_COLOR,
                 anchor="e").pack(side="right")

    def _shots_table(self, parent) -> None:
        s  = UI
        st = self._stats

        COL_LABEL = 0
        COL_P1    = 1
        COL_P2    = 2
        NUM_COLS  = 3
        CP        = s.STATS_TABLE_COL_PAD

        frame = tk.Frame(parent, bg=s.BG_COLOR)
        frame.pack(fill="x", padx=s.STATS_ROW_PADX,
                   pady=(s.STATS_TABLE_PADY_TOP, s.STATS_TABLE_PADY_BOT))
        frame.columnconfigure(COL_LABEL, weight=1)

        hdr_kw = dict(font=s.STATS_ROW_VALUE_FONT, fg=s.STATS_ROW_VALUE_COLOR, bg=s.BG_COLOR)
        lbl_kw = dict(font=s.STATS_ROW_LABEL_FONT, fg=s.STATS_ROW_LABEL_COLOR, bg=s.BG_COLOR)
        val_kw = dict(font=s.STATS_ROW_VALUE_FONT, fg=s.STATS_ROW_VALUE_COLOR, bg=s.BG_COLOR)

        p1_lbl = self._player_display_name(PLAYER_1)
        p2_lbl = self._player_display_name(PLAYER_2)

        tk.Label(frame, text="",      **lbl_kw).grid(row=0, column=COL_LABEL, sticky="w")
        tk.Label(frame, text=p1_lbl,  **hdr_kw).grid(row=0, column=COL_P1, padx=(CP, 0), sticky="e")
        tk.Label(frame, text=p2_lbl,  **hdr_kw).grid(row=0, column=COL_P2, padx=(CP, 0), sticky="e")

        div_pady = s.STATS_TABLE_DIVIDER_PADY
        tk.Frame(frame, height=1, bg=s.STATS_DIVIDER_COLOR).grid(
            row=1, column=COL_LABEL, columnspan=NUM_COLS,
            sticky="ew", pady=(div_pady, div_pady))

        rows = [
            (CT.STATS_ROW_SHOTS_P1,   str(st.shots(PLAYER_1)),   str(st.shots(PLAYER_2))),
            (CT.STATS_ROW_WINNING_SHOT,
             str(st.hits(PLAYER_1)),   str(st.hits(PLAYER_2))),
        ]
        for i, (label, v1, v2) in enumerate(rows):
            r = i + 2
            tk.Label(frame, text=label, **lbl_kw).grid(row=r, column=COL_LABEL, sticky="w", pady=s.STATS_ROW_PADY)
            tk.Label(frame, text=v1,    **val_kw).grid(row=r, column=COL_P1, padx=(CP, 0), sticky="e", pady=s.STATS_ROW_PADY)
            tk.Label(frame, text=v2,    **val_kw).grid(row=r, column=COL_P2, padx=(CP, 0), sticky="e", pady=s.STATS_ROW_PADY)

    def _winner_text(self) -> str:
        st = self._stats
        if st.winner == PLAYER_1:
            if self._human_player == PLAYER_1:
                return CT.STATS_WINNER_HUMAN
            return CT.STATS_WINNER_P1
        if st.winner == PLAYER_2:
            if self._human_player == PLAYER_2:
                return CT.STATS_WINNER_HUMAN
            if self._human_player == PLAYER_1:
                return CT.STATS_WINNER_AI
            return CT.STATS_WINNER_P2
        return CT.STATS_WINNER_DRAW

    def _player_display_name(self, player: int) -> str:
        if self._human_player == player:
            return CT.PLAYER_HUMAN
        if self._human_player is not None:
            return CT.PLAYER_AI
        return (CT.PLAYER_1_NAME if player == PLAYER_1 else CT.PLAYER_2_NAME)

    def _build_chart(self, parent) -> None:
        s  = UI
        st = self._stats

        history = st.advantage_history
        if not history:
            return

        xs     = [h[0] for h in history]
        scores = [h[1] for h in history]

        fig, ax = plt.subplots(figsize=(
            (s.STATS_WINDOW_WIDTH - 2 * s.STATS_PADDING) / s.STATS_CHART_DPI,
            s.STATS_CHART_HEIGHT_IN,
        ), dpi=s.STATS_CHART_DPI)
        fig.patch.set_facecolor(s.STATS_CHART_BG)
        ax.set_facecolor(s.STATS_CHART_BG)

        positive = [max(v, 0) for v in scores]
        negative = [min(v, 0) for v in scores]

        ax.plot(xs, scores,
                color=s.STATS_CHART_LINE_COLOR,
                lw=s.STATS_CHART_LINE_WIDTH,
                marker="o", markersize=2)
        ax.fill_between(xs, positive,
                        alpha=s.STATS_CHART_FILL_ALPHA,
                        color=s.STATS_CHART_P1_COLOR,
                        label=CT.STATS_CHART_P1_LABEL)
        ax.fill_between(xs, negative,
                        alpha=s.STATS_CHART_FILL_ALPHA,
                        color=s.STATS_CHART_P2_COLOR,
                        label=CT.STATS_CHART_P2_LABEL)

        ax.axhline(0, color=s.STATS_CHART_ZERO_COLOR,
                   lw=s.STATS_CHART_ZERO_WIDTH, linestyle=":",
                   label=CT.STATS_CHART_ZERO_LABEL)

        ax.set_xlabel(CT.STATS_CHART_X_LABEL,
                      fontsize=s.STATS_CHART_FONT_SIZE,
                      color=s.STATS_CHART_TEXT_COLOR,
                      labelpad=s.STATS_CHART_LABEL_PAD)
        ax.set_ylabel(CT.STATS_CHART_Y_LABEL,
                      fontsize=s.STATS_CHART_FONT_SIZE,
                      color=s.STATS_CHART_TEXT_COLOR,
                      labelpad=s.STATS_CHART_LABEL_PAD)
        ax.tick_params(labelsize=s.STATS_CHART_FONT_SIZE,
                       length=s.STATS_CHART_TICK_LENGTH,
                       pad=s.STATS_CHART_TICK_PAD,
                       colors=s.STATS_CHART_TEXT_COLOR)
        for sp in ax.spines.values():
            sp.set_edgecolor(s.STATS_CHART_TEXT_COLOR)
            sp.set_linewidth(s.STATS_CHART_SPINE_WIDTH)
        ax.grid(True, color=s.STATS_CHART_GRID_COLOR,
                lw=s.STATS_CHART_GRID_WIDTH, linestyle=":")
        ax.legend(fontsize=s.STATS_CHART_FONT_SIZE,
                  facecolor=s.STATS_CHART_BG,
                  edgecolor=s.STATS_CHART_TEXT_COLOR,
                  labelcolor=s.STATS_CHART_TEXT_COLOR)
        fig.tight_layout(pad=s.STATS_CHART_LAYOUT_PAD)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", pady=(s.STATS_CHART_PACK_PADY_TOP, 0))
        plt.close(fig)

    def _build_progress_chart(self, parent) -> None:
        s  = UI
        st = self._stats

        h1 = st.progress_history(PLAYER_1)
        h2 = st.progress_history(PLAYER_2)
        if not h1 and not h2:
            return

        fig, ax = plt.subplots(figsize=(
            (s.STATS_WINDOW_WIDTH - 2 * s.STATS_PADDING) / s.STATS_CHART_DPI,
            s.STATS_CHART2_HEIGHT_IN,
        ), dpi=s.STATS_CHART_DPI)
        fig.patch.set_facecolor(s.STATS_CHART_BG)
        ax.set_facecolor(s.STATS_CHART_BG)

        if h1:
            xs1 = [p[0] for p in h1]
            ys1 = [p[1] for p in h1]
            ax.plot(xs1, ys1, color=s.STATS_CHART_P1_COLOR,
                    lw=s.STATS_CHART_LINE_WIDTH,
                    marker="o", markersize=2,
                    label=CT.STATS_CHART_P1_LABEL)
        if h2:
            xs2 = [p[0] for p in h2]
            ys2 = [p[1] for p in h2]
            ax.plot(xs2, ys2, color=s.STATS_CHART_P2_COLOR,
                    lw=s.STATS_CHART_LINE_WIDTH,
                    marker="o", markersize=2,
                    label=CT.STATS_CHART_P2_LABEL)

        ax.set_title(CT.STATS_CHART2_TITLE,
                     fontsize=s.STATS_CHART_FONT_SIZE,
                     color=s.STATS_CHART_TEXT_COLOR)
        ax.set_xlabel(CT.STATS_CHART2_X_LABEL,
                      fontsize=s.STATS_CHART_FONT_SIZE,
                      color=s.STATS_CHART_TEXT_COLOR,
                      labelpad=s.STATS_CHART_LABEL_PAD)
        ax.set_ylabel(CT.STATS_CHART2_Y_LABEL,
                      fontsize=s.STATS_CHART_FONT_SIZE,
                      color=s.STATS_CHART_TEXT_COLOR,
                      labelpad=s.STATS_CHART_LABEL_PAD)
        ax.set_ylim(0, 100)
        ax.tick_params(labelsize=s.STATS_CHART_FONT_SIZE,
                       length=s.STATS_CHART_TICK_LENGTH,
                       pad=s.STATS_CHART_TICK_PAD,
                       colors=s.STATS_CHART_TEXT_COLOR)
        for sp in ax.spines.values():
            sp.set_edgecolor(s.STATS_CHART_TEXT_COLOR)
            sp.set_linewidth(s.STATS_CHART_SPINE_WIDTH)
        ax.grid(True, color=s.STATS_CHART_GRID_COLOR,
                lw=s.STATS_CHART_GRID_WIDTH, linestyle=":")
        ax.legend(fontsize=s.STATS_CHART_FONT_SIZE,
                  facecolor=s.STATS_CHART_BG,
                  edgecolor=s.STATS_CHART_TEXT_COLOR,
                  labelcolor=s.STATS_CHART_TEXT_COLOR)
        fig.tight_layout(pad=s.STATS_CHART_LAYOUT_PAD)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", pady=(s.STATS_CHART_PACK_PADY_TOP, 0))
        plt.close(fig)

    def _center(self, parent) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w  = self.winfo_reqwidth()
        h  = self.winfo_reqheight()
        x  = px + (pw - w) // 2
        y  = py + (ph - h) // 2
        self.geometry("+" + str(x) + "+" + str(y))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _fmt_dur(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    if m:
        return str(m) + "m " + str(s).zfill(2) + "s"
    return str(s) + "s"


def _fmt_pct(value: float) -> str:
    return str(round(value * 100)) + "%"
