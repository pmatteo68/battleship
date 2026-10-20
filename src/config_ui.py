"""
UI skin selector for Battleship.
Set SKIN to the name of a module inside src/skins/ to switch the active skin.
"""
import importlib
import logging
import random

logger = logging.getLogger(__name__)

SKINS = (
    "default",          # Default        - navy blue ocean theme
    "midnight",         # Midnight       - near-black, neon markers, dark-mode
    "ocean",            # Ocean          - deep teal and cyan on dark navy
    "sunset",           # Sunset         - amber/coral warm tones
    "forest",           # Forest         - mossy greens, bark browns
    "candy",            # Candy          - pastel bubblegum palette
    "vivid_1",          # Vivid-1        - full-saturation primaries on white
    "vivid_2",          # Vivid-2        - electric cobalt+cyan on pale blue
    "mint_gray",        # Mint-Gray      - cool gray canvas, mint accents
    "black_and_white",  # B&W            - pure monochrome grayscale
)

# Active skin -- replace "default" with any name above, or use "random"
SKIN = "default"

try:
    SKIN = random.choice(SKINS) if SKIN == "random" else SKIN
    _skin = importlib.import_module(f"skins.{SKIN}")
except (ImportError, ValueError) as _err:
    logger.error("Skin '%s' could not be loaded (%s) -- falling back to default", SKIN, _err)
    from skins import default as _skin


def get_name() -> str:
    return _skin.SKIN_NAME


# Layout constants not defined per-skin; skins may override any of these.
_DEFAULTS = {
    "RULES_WRAP_WIDTH":             500,
    "RULES_LABEL_PADX":             24,
    "RULES_LABEL_PADY":             16,
    "RULES_CLOSE_PADY_BOT":         16,
    "STATS_SECTION_PACK_PADY_TOP":  8,
    "STATS_SECTION_PACK_PADY_BOT":  2,
    "STATS_CLOSE_BTN_PADY_TOP":     8,
    "STATS_CHART_PACK_PADY_TOP":    8,
    "STATS_TABLE_PADY_TOP":         4,
    "STATS_TABLE_PADY_BOT":         2,
    "STATS_TABLE_COL_PAD":          24,
    "STATS_TABLE_DIVIDER_PADY":     3,
    "STATUS_BTN_FONT":              ("Helvetica", 9),
    "MIN_WINDOW_WIDTH":             900,
    "PLACEMENT_SHIP_LIST_WIDTH":    160,
    "SHIP_TABLE_HEADING_BG":        "#1565c0",
    "SHIP_TABLE_HEADING_FG":        "#ffffff",
    "SHIP_TABLE_ROW_ACTIVE_BG":     "#ddeeff",
    "SHIP_TABLE_ROW_ACTIVE_FG":     "#0d47a1",
    "SHIP_TABLE_ROW_DONE_BG":       "#f5f5f5",
    "SHIP_TABLE_ROW_DONE_FG":       "#b0bec5",
    "SHIP_TABLE_SELECT_BG":         "#1565c0",
    "SHIP_TABLE_SELECT_FG":         "#ffffff",
    "SHIP_TABLE_VISIBLE_ROWS":      6,
    "SHIP_TABLE_COL_TYPE_W":        160,
    "SHIP_TABLE_COL_COUNT_W":       55,
    "GRID_INTER_PAD":               20,
    "START_ENGINE_LABEL_PADY_TOP":  2,
    "FLEET_PREVIEW_CELL_SIZE":      20,
    "FLEET_PREVIEW_CELL_GAP":       2,
    "FLEET_PREVIEW_BOX_W":          100,
    "FLEET_PREVIEW_BOX_H":          60,
    "FLEET_PREVIEW_ROW_PADY":       6,
    "FLEET_PREVIEW_OFFSET_X":       12,
    "FLEET_MISS_MARK_COLOR":        "#7896b0",
    "FLEET_MISS_MARK_FONT":         ("Helvetica", 8, "bold"),
    "LIVE_STATS_FONT":              ("Helvetica", 9),
    "LIVE_STATS_COLOR":             "#4a6080",
    "LIVE_STATS_PANEL_PADX":        6,
    "LIVE_STATS_PANEL_PADY":        3,
    "LIVE_STATS_PANEL_SEP_H":       5,   # height of the divider between metric groups
    "STATS_CHART2_HEIGHT_IN":       2.0,
    "STATS_SHOW_PROGRESS_CHART":    True,
}


def __getattr__(name: str):
    try:
        return getattr(_skin, name)
    except AttributeError:
        if name in _DEFAULTS:
            return _DEFAULTS[name]
        raise
