from __future__ import annotations

import argparse
import os

from sub_d_tester.config import DEFAULT_BAUDRATE, DEFAULT_PORT_UNIX, DEFAULT_PORT_WINDOWS
from sub_d_tester.ui import starte_app


def standard_port() -> str:
    return DEFAULT_PORT_WINDOWS if os.name == "nt" else DEFAULT_PORT_UNIX


def argumente_lesen() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="Sub-D-Tester")
    parser.add_argument("--port", default=standard_port(), help="Serieller Port, zum Beispiel COM7 oder /dev/ttyACM0")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="Baudrate für die Arduino-Verbindung")
    parser.add_argument("--fenster", action="store_true", help="Im Fenstermodus statt im Vollbild starten")
    parser.add_argument("--simulation", action="store_true", help="Ohne Hardware mit simulierten Prüfergebnissen starten")
    return parser.parse_args()


def main() -> None:
    argumente = argumente_lesen()
    starte_app(
        port=argumente.port,
        baudrate=argumente.baudrate,
        fenster=argumente.fenster,
        simulation=argumente.simulation,
    )


if __name__ == "__main__":
    main()
