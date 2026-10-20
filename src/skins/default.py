"""Default skin -- classic navy theme."""

SKIN_NAME = "Default"

# -- Window / chrome -----------------------------------------------------------
BG_COLOR         = "#f0f4f8"
PANEL_BG         = "#f0f4f8"
TEXT_COLOR       = "#1a3a5c"
TEXT_SECONDARY   = "#607d8b"
BUTTON_BG        = "#1565c0"
BUTTON_FG        = "#ffffff"
BUTTON_ACTIVE_BG = "#1976d2"
ACCENT_COLOR     = "#1565c0"

# -- Grid geometry (pixels) ----------------------------------------------------
CELL_SIZE    = 38
BOARD_PADDING = 12
LABEL_AREA_W = 22
LABEL_AREA_H = 22

# -- Grid cell colors ----------------------------------------------------------
FLEET_WATER_COLOR    = "#ddeeff"
ATTACK_UNKNOWN_COLOR = "#e8edf2"
SHIP_COLOR           = "#607d8b"
HIT_COLOR            = "#e53935"
MISS_COLOR           = "#b0bec5"
SUNK_COLOR           = "#880e0e"
GHOST_VALID_COLOR    = "#80cbc4"
GHOST_INVALID_COLOR  = "#ef9a9a"

# -- Flash colors --------------------------------------------------------------
HIT_FLASH_COLOR    = "#ff5252"
MISS_FLASH_COLOR   = "#e0e0e0"
SUNK_FLASH_COLOR   = "#ff1744"
WIN_FLASH_COLOR_P1 = "#1565c0"
WIN_FLASH_COLOR_P2 = "#fdd835"

# -- Grid labels ---------------------------------------------------------------
LABEL_FONT        = ("Helvetica", 8)
LABEL_COLOR       = "#455a64"
GRID_BORDER_COLOR = "#1565c0"
CELL_OUTLINE_COLOR = "#c5cdd8"

# -- Ship list (placement panel) -----------------------------------------------
SHIP_LIST_BG          = "#e8edf2"
SHIP_LIST_SELECTED_BG = "#1565c0"
SHIP_LIST_SELECTED_FG = "#ffffff"
SHIP_LIST_NORMAL_FG   = "#1a3a5c"
SHIP_LIST_FONT        = ("Helvetica", 9)

# -- Fonts ---------------------------------------------------------------------
TITLE_FONT       = ("Helvetica", 22, "bold")
SUBTITLE_FONT    = ("Helvetica", 11)
STATUS_FONT      = ("Helvetica", 10)
BUTTON_FONT      = ("Helvetica", 10)
HEADER_FONT      = ("Helvetica", 12, "bold")
STATS_LABEL_FONT = ("Helvetica", 9)
STATS_VALUE_FONT = ("Helvetica", 9, "bold")

# -- Misc ----------------------------------------------------------------------
RELIEF       = "flat"
BORDER_WIDTH = 1
PAD_X        = 8
PAD_Y        = 6
SPLASH_BG    = "#f0f4f8"

# -- Stats chart ---------------------------------------------------------------
CHART_BG         = "#f0f4f8"
CHART_AXES_BG    = "#e8edf2"
CHART_LINE_COLOR = "#1565c0"
CHART_ZERO_COLOR = "#b0bec5"
CHART_TEXT_COLOR = "#455a64"

# -- Window layout -------------------------------------------------------------
WINDOW_WIDTH          = 1000
WINDOW_HEIGHT         = 680
LAYOUT_INIT_DELAY_MS  = 10

# -- Status bar ----------------------------------------------------------------
STATUS_BAR_HEIGHT   = 44
STATUS_BG           = "#dde5f0"
STATUS_COLOR        = "#1a3a5c"
STATUS_LABEL_PADX   = 12
STATUS_BTN_PADX     = 4
STATUS_BTN_PADX_END = 8
STATUS_BTN_PADY     = 4
STATUS_BTN_FONT     = ("Helvetica", 9)

# -- Buttons -------------------------------------------------------------------
BTN_BG        = "#1565c0"
BTN_FG        = "#ffffff"
BTN_ACTIVE_BG = "#1976d2"
BTN_FONT      = ("Helvetica", 11, "bold")
BTN_RELIEF    = "flat"
BTN_PADX      = 14
BTN_PADY      = 6
BTN_BD        = 0
MENU_BD       = 0

# -- Start screen --------------------------------------------------------------
START_TITLE_FONT     = ("Helvetica", 28, "bold")
START_TITLE_COLOR    = "#1565c0"
START_SUBTITLE_FONT  = ("Helvetica", 13)
START_SUBTITLE_COLOR = "#455a64"
START_BTN_PADX       = 8
START_TITLE_PADY     = 8
START_SUBTITLE_PADY  = 16
START_SECTION_PADY   = 14
START_WHO_FIRST_PADY = 12
START_BOTTOM_ROW_PADY= 12

LABEL_FONT  = ("Helvetica", 11)
LABEL_COLOR = "#455a64"

# -- Menu colors ---------------------------------------------------------------
MENU_FG = "#1a3a5c"

# -- About / Rules dialogs -----------------------------------------------------
ABOUT_WRAP_WIDTH     = 400
ABOUT_PADX           = 24
ABOUT_PADY           = 8
ABOUT_TITLE_PADY_TOP = 20
ABOUT_CLOSE_PADY_BOT = 20
RULES_WRAP_WIDTH     = 420
RULES_LABEL_PADX     = 24
RULES_LABEL_PADY     = 16
RULES_CLOSE_PADY_BOT = 16

# -- Stats window --------------------------------------------------------------
STATS_WINDOW_WIDTH      = 600
STATS_PADDING           = 18
STATS_TITLE_PADY_BOT    = 10
STATS_CLOSE_SPACER_H    = 6
STATS_SECTION_BG        = "#1565c0"
STATS_SECTION_FG        = "#ffffff"
STATS_SECTION_FONT      = ("Helvetica", 10, "bold")
STATS_SECTION_PADY      = 6
STATS_ROW_LABEL_FONT    = ("Helvetica", 10)
STATS_ROW_VALUE_FONT    = ("Helvetica", 10, "bold")
STATS_ROW_LABEL_COLOR   = "#1a3a5c"
STATS_ROW_VALUE_COLOR   = "#1565c0"
STATS_ROW_PADX          = 14
STATS_ROW_PADY          = 2
STATS_DIVIDER_COLOR     = "#b0bec5"
STATS_TITLE_FONT        = ("Helvetica", 20, "bold")
STATS_TITLE_COLOR       = "#1565c0"
STATS_DELAY_MS          = 800
STATS_SHOW_CHART        = True
STATS_CHART_HEIGHT_IN   = 2.6
STATS_CHART_DPI         = 90
STATS_CHART_BG          = "#f0f4f8"
STATS_CHART_P1_COLOR    = "#1565c0"
STATS_CHART_P2_COLOR    = "#fdd835"
STATS_CHART_LINE_COLOR  = "#455a64"
STATS_CHART_ZERO_COLOR  = "#b0bec5"
STATS_CHART_TEXT_COLOR  = "#455a64"
STATS_CHART_GRID_COLOR  = "#d0dae6"
STATS_CHART_FILL_ALPHA  = 0.20
STATS_CHART_LINE_WIDTH  = 1.8
STATS_CHART_ZERO_WIDTH  = 1.0
STATS_CHART_FONT_SIZE   = 7
STATS_CHART_LABEL_PAD   = 2
STATS_CHART_TICK_LENGTH = 3
STATS_CHART_TICK_PAD    = 2
STATS_CHART_SPINE_WIDTH = 0.8
STATS_CHART_GRID_WIDTH  = 0.5
STATS_CHART_LAYOUT_PAD  = 0.6
STATS_SECTION_PACK_PADY_TOP = 8
STATS_SECTION_PACK_PADY_BOT = 2
STATS_CLOSE_BTN_PADY_TOP    = 8
STATS_CHART_PACK_PADY_TOP   = 8

# -- Misc layout ---------------------------------------------------------------
PANEL_DIVIDER_COLOR  = "#c0ccd8"
BOARD_BORDER         = "#b0bec5"
TURN_COLOR_P1        = "#1565c0"
TURN_COLOR_P2        = "#c62828"

# -- Ship deployment table (placement panel) -----------------------------------
SHIP_TABLE_HEADING_BG    = "#1565c0"   # column header background
SHIP_TABLE_HEADING_FG    = "#ffffff"   # column header text
SHIP_TABLE_ROW_ACTIVE_BG = "#ddeeff"   # row still has ships to deploy (Left > 0)
SHIP_TABLE_ROW_ACTIVE_FG = "#0d47a1"   # text for active rows (prominent)
SHIP_TABLE_ROW_DONE_BG   = "#f5f5f5"   # row fully deployed (Left = 0, dimmed)
SHIP_TABLE_ROW_DONE_FG   = "#b0bec5"   # text for done rows (muted)
SHIP_TABLE_SELECT_BG     = "#1565c0"   # selected row highlight background
SHIP_TABLE_SELECT_FG     = "#ffffff"   # selected row highlight text
SHIP_TABLE_VISIBLE_ROWS  = 6           # visible rows before scrolling
SHIP_TABLE_COL_TYPE_W    = 160         # pixel width of the Type column
SHIP_TABLE_COL_COUNT_W   = 55          # pixel width of Deployed and Left columns
