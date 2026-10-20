# Battleship

> **Version:** 1.0.0
> **Date:** Oct. 20, 2026
> **Author:** Matteo P.
> **URL:** https://github.com/pmatteo68/battleship
---

## Abstract

A desktop implementation of Battleshipbuilt with Python
and Tkinter.  Two players each secretly place a fleet of ships on their private
grid.  Players then alternate firing shots at the enemy grid, trying to sink
the entire fleet.  A shot that lands on a ship cell is a HIT; otherwise it is
a MISS.  When every cell of a ship is hit, the ship is SUNK.  The first player
to sink all of the opponent's ships wins.

The computer opponent uses a Hunt-and-Target strategy with optional probability
density heatmaps to optimise shot selection.  An autoplay mode runs a fully
unattended game from start to finish, exercising the complete game flow
including the end-of-game statistics window.

The game runs fully offline with no dependency on external services.

---

## Setup

### Prerequisites

Python is not assumed to be on the system PATH.  The path to the Python
interpreter is configured in `bin\env.cmd` (Windows) or `bin/env.sh`
(Unix/macOS).  Edit those files if your Python installation is in a different
location before running any script.

### 1. Create the virtual environment (once)

Open a terminal inside the `v<X.Y.Z>` directory and run the setup script.

**Windows:**

```
create_env.cmd
```

**Unix / macOS:**

```
bash create_env.sh
```

The script puts Python on the PATH, creates a virtual environment, activates
it, and installs the dependencies listed in `requirements.txt`.  If the
virtual environment already exists the script simply activates it without
reinstalling anything.

### 2. Launch the game

Run the play script every time you want to start the game.

**Windows:**

```
play.cmd
```

**Unix / macOS:**

```
bash play.sh
```

### Optional: open an environment-ready shell (Windows only)

```
open_env.cmd
```

Opens a new CMD window.  You can then run `bin\env` manually and work
interactively with the Python environment.

---

## How to play

### Human vs. Machine

1. Launch the game.
2. On the start screen choose grid size, fleet preset, and who fires first.
3. Click **?** next to the fleet label to preview the ship shapes and counts
   for the selected preset.  Then click **Start Game**.
4. **Placement phase** -- click cells on your fleet grid to place ships one at
   a time.  Press **R** or click **Rotate** to cycle through available
   rotations (straight ships have 2; asymmetric ships have up to 4).
   Click **Random Place** to have the AI place your whole fleet at once.
   When all ships are placed click **Confirm Fleet**.
5. The machine places its ships automatically.
6. **Attack phase** -- click a cell on the right-hand grid (Enemy Waters) to
   fire a shot.  Wait for the machine to reply.  Repeat until one fleet is
   fully sunk.  A live stats panel shows real-time Shots, Hits, Progress,
   Accuracy, and per-ship-type sunk counts for both players; its position
   (between the grids or to their right) is configurable in `config_game.py`.
   Cells where the opponent missed can optionally be marked on your fleet grid
   (also a toggle in `config_game.py`).
7. A game summary window appears at the end with statistics, a fleet-advantage
   chart, and a hit-progress chart showing how each player's progress evolved
   shot by shot.

### Autoplay mode

Click **Auto Play** on the start screen.  Both players are controlled by the
AI engine.  No human interaction is required.  The full game plays out
automatically and the stats window is shown at the end.

### Save and load

Use **Save Game** (menu or button) to save the current game state to a JSON
file.  Use **Load Game** to resume a saved game at any time.

---

## Configuration

All game parameters, text labels, and visual settings are externalised into
configuration files.  No numeric constant is hard-coded in the source.

### Game parameters -- `src/config_game.py`

This file centralises every tunable gameplay constant:

- **Grid**: default dimensions and hard min/max limits (rows and columns).
- **Fleet**: the active preset name and the full preset catalog (see below).
- **AI engine**: which engine module to load from `src/ai_engines/`.
- **Timing and animation**: delays before the AI fires, between moves, and
  during autoplay; flash counts and intervals for hit, miss, sunk, and win
  events; the extra hold time that keeps result messages readable.
- **Display toggles**: whether opponent-missed cells are marked on the fleet
  grid; whether the live stats panel sits between the two grids or to their
  right.
- **Scoring**: scale factor used by the advantage chart algorithm.

Every constant is annotated inline; hard limits are documented where they apply.

### Ship types -- `src/config_ships.py`

Each ship type is a name mapped to a shape: a list of `[row_offset, col_offset]`
cell coordinates relative to an anchor at `[0, 0]`.  Shapes must be
orthogonally 4-connected.  The engine derives all distinct 90-degree rotations
automatically.

```python
# Example: L-shaped 3-cell ship
"My Ship": [[0, 0], [0, 1], [1, 0]]
```

To add a new ship type, append an entry here and reference the name in a fleet
preset.

### Fleet presets -- `src/config_game.py`

A fleet preset is a list of `{name, count}` entries.  The name must match a
ship type defined in `config_ships.py`.

```python
"my_preset": [
    {"name": "Carrier",  "count": 1},
    {"name": "My Ship",  "count": 2},
]
```

Add the preset to the catalog and set it as the default in the same file.
Keep total ship cells below roughly half the grid area so random placement
can always find valid positions.

### Visual settings -- `src/config_ui.py`

This file has two settings: the active skin name and the catalog of available
skins.  Set the active skin to any key from the catalog (or `"random"` to
pick a new skin each launch).

### Text labels -- `src/config_text.py`

Every user-visible string is defined here.  Edit this file to relabel,
translate, or rebrand the interface.

---

## Skins

The following built-in skins are available.  Set the active skin in
`src/config_ui.py` to the key name shown.

| Key | Description |
|---|---|
| `default` | Classic navy blue theme |
| `midnight` | Near-black with neon cyan |
| `ocean` | Deep blue water, coral ships |
| `sunset` | Warm peach and gold tones |
| `forest` | Dark green, lime accents |
| `candy` | Pastel pink and purple |
| `vivid_1` | Bright primary colors |
| `vivid_2` | Deep purple, electric blue |
| `mint_gray` | Mint green and professional gray |
| `black_and_white` | Pure monochrome |

A skin file is a plain Python module in `src/skins/` that defines all visual
constants.  Copy `src/skins/default.py` to `src/skins/my_skin.py`, edit the
color values, then register the new name in the skin catalog and activate it
in `src/config_ui.py`.

---

## AI plugin system

The AI engine is fully pluggable.  The active engine is named in
`src/config_game.py` as a module name (no `.py` suffix) inside `src/ai_engines/`.

### Built-in engine: `hunt_target`

The Hunt-and-Target strategy works in two modes:

- **Hunt mode** -- no known active hit.  Computes a probability density map
  by counting how many valid placements of each remaining ship would cover
  each unknown cell.  Fires at the highest-scoring cell.  Optionally
  restricted to a checkerboard pattern (since every ship of size >= 2 must
  span at least one cell of each parity).

- **Target mode** -- one or more active hits (cells belonging to a ship that
  has not yet been sunk).  Extends the known hit run in its direction first;
  falls back to all adjacent unknown cells if no directional extension is
  available.

A dedicated config file inside `src/ai_engines/` lets you tune three
behavioural knobs: whether hunt mode uses the checkerboard restriction;
whether probability density scoring is used versus uniform random; and whether
target mode prioritises run extension over scattered adjacent probing.

### Writing a custom AI engine

1. Create `src/ai_engines/my_engine.py`.
2. Import and subclass `BattleshipAIEngine` from `src/ai_engines/base.py`.
3. Implement the three abstract methods:

```python
from ai_engines.base import BattleshipAIEngine, _random_placement

class MyEngine(BattleshipAIEngine):

    def get_name(self) -> str:
        return "My Custom Engine"

    def reset(self) -> None:
        # Clear any internal state before a new game
        pass

    def _compute_placement(self, num_rows, num_cols, flat_fleet):
        # flat_fleet: list of {"name": str, "shape": list} dicts
        # Return:     list of (row, col, shape) tuples, same order;
        #             shape is a rotated variant of the canonical ship shape.
        return _random_placement(num_rows, num_cols, flat_fleet)

    def _compute_next_attack(self, attack_board, num_rows, num_cols,
                              remaining_shapes, sunk_ships):
        # attack_board[row][col]: 0=unknown, 1=miss, 2=hit
        # remaining_shapes: list of shapes for unsunk ships (list of [dr,dc])
        # sunk_ships:       list of PlacedShip objects already sunk
        # Return:           (row, col) of a cell where attack_board == 0
        import random
        valid = [(r, c)
                 for r in range(num_rows)
                 for c in range(num_cols)
                 if attack_board[r][c] == 0]
        return random.choice(valid)


def create() -> MyEngine:
    return MyEngine()
```

4. Set the engine name to `"my_engine"` in `src/config_game.py`.

The base class wraps your implementation with validation and falls back to
random placement or a random shot if your method returns an invalid value,
so the game never crashes due to a buggy plugin.

---

## Save file format

Saved games are standard JSON files.  The `docs/` directory contains a fully
annotated example that serves as the authoritative format reference.

---

## Logging

Log output is written to a file in the working directory.  The log level is
controlled by the `GAME_LOG_LEVEL` environment variable (default `INFO`,
configured in the env scripts under `bin/`).

All game events are logged at DEBUG level.  The start banner and the
final game-summary lines are logged at INFO level.

To see all debug output, set `GAME_LOG_LEVEL=DEBUG` in the env script or
your shell before launching.

---

## Project structure

```
v<X.Y.Z>/
  battleship.py          -- top-level launcher
  play.cmd / play.sh     -- launch scripts
  create_env.cmd / .sh   -- virtual environment setup
  open_env.cmd           -- Windows: opens a ready CMD window
  bin/                   -- Python PATH and env-var configuration
  requirements.txt       -- pip dependencies
  docs/                  -- annotated save-file example
  src/
    main.py              -- entry point and logging setup
    config_game.py       -- game parameters and fleet presets
    config_ships.py      -- ship type catalog (names and shapes)
    config_ui.py         -- skin selector
    config_text.py       -- all user-visible text
    game_logic.py        -- board model, placement, and attack logic
    game_persistence.py  -- JSON save / load
    game_stats.py        -- statistics collector
    ai_engine.py         -- AI facade
    ui_main.py           -- main window and phase controller
    ui_board.py          -- board and placement UI components
    ui_stats.py          -- end-of-game statistics window and charts
    ai_engines/          -- pluggable AI engines (currently: Hunt-and-Target)
    skins/               -- visual theme files (one Python module per skin)
```

---

## Dependencies

- Python 3.8 or later
- All other dependencies: see `requirements.txt`.
