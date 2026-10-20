"""Entry point for Battleship."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# DPI awareness on Windows (must be called before Tkinter is imported)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

import logging
import log_config
import sw_metadata as META

log_config.setup()
log = logging.getLogger(__name__)


def main() -> None:
    import config_game  as CG
    import config_ui    as CUI
    import ai_engine    as AE
    import config_ships as CS
    from game_logic import validate_shape

    for _ship_name, _ship_shape in CS.SHIP_TYPES.items():
        validate_shape(_ship_shape)

    log.info("=" * 60)
    log.info("%s  v. %s  --  starting", META.getSWName(), META.getVersion())
    log.info("Python %s  |  platform: %s", sys.version.split()[0], sys.platform)
    log.info("AI: %s  |  Skin: %s", AE.get_name(), CUI.get_name())
    log.info(
        "Grid defaults: %dx%d  fleet: %s",
        CG.GRID_COLS_DEFAULT, CG.GRID_ROWS_DEFAULT,
        CG.FLEET_PRESET_DEFAULT,
    )
    log.info("=" * 60)

    from ui_main import App
    app = App()
    app.mainloop()

    log.info("=" * 60)
    log.info("%s  --  exited normally", META.getSWName())
    log.info("=" * 60)


if __name__ == "__main__":
    main()
