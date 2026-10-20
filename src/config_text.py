"""All user-visible text for Battleship -- change here to localise or rebrand."""

from sw_metadata import getSWName, getVersion
from config_game import (
    GRID_ROWS_DEFAULT,
    GRID_COLS_DEFAULT,
    FLEET_PRESET_DEFAULT,
    NUM_PLAYERS,
)
import ai_engine

# -- Window -------------------------------------------------------------------
WINDOW_TITLE = getSWName() + " v. " + getVersion()

# -- Start screen -------------------------------------------------------------
START_TITLE        = getSWName()
START_SUBTITLE     = "Sink the enemy fleet!"
START_ENGINE_LABEL = "AI engine:"
START_WHO_FIRST    = "Who attacks first?"
START_FIRST_HUMAN  = "  Human  "
START_FIRST_AI     = "  Machine  "
START_ROWS_LABEL   = "Grid rows:"
START_COLS_LABEL   = "Grid cols:"
START_FLEET_LABEL  = "Fleet preset:"

def make_rules_hint(num_rows, num_cols, fleet_preset):
    return (
        str(num_cols) + "x" + str(num_rows) + " grid  |  fleet: " + fleet_preset
    )

# -- Buttons ------------------------------------------------------------------
BTN_START         = "  Start Game  "
BTN_CLOSE         = "  Close  "
BTN_NEW_GAME      = "New Game"
BTN_SAVE_GAME     = "Save Game"
BTN_LOAD_GAME     = "Load Game"
BTN_AUTOPLAY      = "  Auto Play  "
BTN_EXIT          = "Exit"
BTN_QUIT          = "Quit"
BTN_FLEET_PREVIEW      = "?"
FLEET_PREVIEW_TITLE    = "Fleet preview: {preset}"
FLEET_PREVIEW_SUBTITLE = "One item of each ship type shown in its canonical orientation."

BTN_ROTATE        = "Rotate (R)"
BTN_RANDOM_PLACE  = "Random Place"
BTN_UNDO_PLACE    = "Undo Last"
BTN_CONFIRM_FLEET = "Confirm Fleet"
BTN_CLEAR_FLEET   = "Clear All"

# -- Player names -------------------------------------------------------------
PLAYER_1_NAME = "Player 1"
PLAYER_2_NAME = "Player 2"
PLAYER_HUMAN  = "Human"
PLAYER_AI     = "Machine"

# -- Placement phase ----------------------------------------------------------
STATUS_PLACEMENT_FMT   = "{name}: place your ships"
STATUS_AI_PLACING      = "Machine is placing ships..."
STATUS_PLACE_SHIP      = "Click grid to place {name} (size {size})"
STATUS_ROTATE_HINT     = "Press R or click Rotate to change orientation"
STATUS_FLEET_READY     = "Fleet ready -- click Confirm Fleet to proceed"
PLACEMENT_TITLE_FMT    = "{name} -- Place Your Fleet"
PLACEMENT_DEPLOY_HEADER  = "Ships deployment"
PLACEMENT_COL_TYPE       = "Type"
PLACEMENT_COL_DEPLOYED   = "Deployed"
PLACEMENT_COL_LEFT       = "Left"
PLACEMENT_ORIENT_H        = "Horizontal"
PLACEMENT_ORIENT_V        = "Vertical"
PLACEMENT_ORIENT_FIXED    = "Fixed (no rotation)"
PLACEMENT_ORIENT_ROTATION = "Rotation {idx}/{total}"

# -- Live stats panel (compact table shown between/beside grids during attack) --
LIVE_STATS_TITLE     = "Stats"
LIVE_STATS_ROW_SHOTS = "Shots"
LIVE_STATS_ROW_HITS  = "Hits"
LIVE_STATS_ROW_PROG  = "Progress"
LIVE_STATS_ROW_ACC   = "Accuracy"

# -- Grid labels --------------------------------------------------------------
GRID_COL_LABELS      = "ABCDEFGHIJKLMNOP"
FLEET_MISS_MARK_TEXT = "x"   # symbol drawn on fleet cells where the opponent missed
LABEL_YOUR_FLEET    = "Your Fleet"
LABEL_ENEMY_WATERS  = "Enemy Waters"
LABEL_P1_FLEET      = "Player 1 Fleet"
LABEL_P1_ATTACKS    = "Player 1 Attacks"
LABEL_P2_FLEET      = "Player 2 Fleet"
LABEL_P2_ATTACKS    = "Player 2 Attacks"

# -- Attack phase status messages ---------------------------------------------
STATUS_HUMAN_TURN   = "Your turn -- click a cell to fire"
STATUS_AI_TURN      = "Machine is thinking..."
STATUS_ANIMATING    = "..."

# -- Attack result messages ---------------------------------------------------
MSG_HIT   = "Hit!"
MSG_MISS  = "Miss."
MSG_SUNK  = "{name} sunk!"

# -- Game-over messages -------------------------------------------------------
GAMEOVER_P1_WINS    = "Player 1 wins!"
GAMEOVER_P2_WINS    = "Player 2 wins!"
GAMEOVER_HUMAN_WINS = "You win!"
GAMEOVER_AI_WINS    = "Machine wins!"
GAMEOVER_DRAW       = "Draw!"

# -- Autoplay -----------------------------------------------------------------
AUTOPLAY_SPLASH_THINKING = "Machine is placing ships..."

# -- Menu labels --------------------------------------------------------------
MENU_GAME  = "Game"
MENU_NEW   = "New Game"
MENU_SAVE  = "Save Game..."
MENU_LOAD  = "Load Game..."
MENU_QUIT  = "Quit"
MENU_HELP  = "Help"
MENU_RULES = "Rules"
MENU_ABOUT = "About..."

# -- Dialog messages ----------------------------------------------------------
MSG_NO_GAME            = "No game in progress."
MSG_SAVED              = "Game saved to:\n{path}"
MSG_SAVE_ERROR         = "Could not save game:\n{err}"
MSG_LOAD_ERROR         = "Could not load game:\n{err}"
MSG_CELL_ALREADY_FIRED = "Already fired at that cell."
SAVE_FILETYPE          = "Battleship saved games (*.json)"

# -- Rules text ---------------------------------------------------------------
RULES_TEXT = (
    getSWName() + "  --  Rules\n\n"
    "Two players each place a fleet of ships on their private grid.\n"
    "Ships can have any orthogonally-connected shape and may be rotated\n"
    "in up to 4 orientations before placing.\n\n"
    "After placement, players alternate firing shots at the enemy grid.\n"
    "A shot is a HIT if it lands on a ship cell, a MISS otherwise.\n"
    "When every cell of a ship is hit, that ship is SUNK.\n\n"
    "The player who sinks the entire enemy fleet wins.\n\n"
    "Standard fleet: Carrier (L-shape, 5 cells), Battleship(4),\n"
    "Destroyer(3), Submarine(3), Patrol Boat(2).\n\n"
    "Default grid: " + str(GRID_COLS_DEFAULT) + " columns x "
    + str(GRID_ROWS_DEFAULT) + " rows, fleet preset: " + FLEET_PRESET_DEFAULT + "."
)

# -- About dialog -------------------------------------------------------------
ABOUT_TITLE    = "About " + getSWName()
ABOUT_SUBTITLE = getSWName()
ABOUT_BODY     = (
    getSWName() + " v. " + getVersion() + "\n\n"
    "A classic naval strategy game.\n\n"
    "AI: " + ai_engine.get_name() + "."
)

# -- Stats window labels ------------------------------------------------------
STATS_TITLE              = "Game Summary"
STATS_SECTION_RESULT     = "RESULT"
STATS_SECTION_SHOTS      = "SHOTS"
STATS_SECTION_ACCURACY   = "ACCURACY"
STATS_SECTION_SHIPS      = "SHIPS SUNK"
STATS_SECTION_TIMING     = "TIMING"

STATS_WINNER_LABEL       = "Winner"
STATS_WINNER_P1          = PLAYER_1_NAME
STATS_WINNER_P2          = PLAYER_2_NAME
STATS_WINNER_HUMAN       = PLAYER_HUMAN
STATS_WINNER_AI          = PLAYER_AI
STATS_WINNER_DRAW        = "Draw"

STATS_ROW_SHOTS_P1       = PLAYER_1_NAME + " shots"
STATS_ROW_SHOTS_P2       = PLAYER_2_NAME + " shots"
STATS_ROW_TOTAL_SHOTS    = "Total shots"
STATS_ROW_WINNING_SHOT   = "Winning shot"

STATS_ROW_ACCURACY_P1    = PLAYER_1_NAME + " accuracy"
STATS_ROW_ACCURACY_P2    = PLAYER_2_NAME + " accuracy"

STATS_ROW_SHIPS_SUNK_P1  = PLAYER_1_NAME + " ships sunk"
STATS_ROW_SHIPS_SUNK_P2  = PLAYER_2_NAME + " ships sunk"
STATS_ROW_STREAK_P1      = PLAYER_1_NAME + " longest hit streak"
STATS_ROW_STREAK_P2      = PLAYER_2_NAME + " longest hit streak"

STATS_DURATION_LABEL     = "Game duration"
STATS_ROW_AVG_TIME_P1    = PLAYER_1_NAME + " avg time/shot"
STATS_ROW_AVG_TIME_P2    = PLAYER_2_NAME + " avg time/shot"
STATS_NA                 = "--"

STATS_CHART_P1_LABEL     = PLAYER_1_NAME
STATS_CHART_P2_LABEL     = PLAYER_2_NAME
STATS_CHART_X_LABEL      = "Shot #"
STATS_CHART_Y_LABEL      = "Fleet advantage (P1)"
STATS_CHART_ZERO_LABEL   = "Equal"

STATS_CHART2_TITLE   = "Hit progress per player"
STATS_CHART2_X_LABEL = "Shot #"
STATS_CHART2_Y_LABEL = "Progress (%)"
