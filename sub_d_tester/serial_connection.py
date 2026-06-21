from __future__ import annotations

import time
from typing import Any

try:
    import serial
except ModuleNotFoundError:
    serial = None


class SerielleVerbindung:
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.anschluss: Any = None
        self.letzter_fehler = ""

    @property
    def verbunden(self) -> bool:
        return self.anschluss is not None and bool(getattr(self.anschluss, "is_open", False))

    def verbinden(self) -> bool:
        self.trennen()
        if serial is None:
            self.letzter_fehler = "pyserial ist nicht installiert. Bitte requirements.txt installieren."
            return False

        try:
            self.anschluss = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2.0)
            self.letzter_fehler = ""
            return True
        except Exception as fehler:
            self.anschluss = None
            self.letzter_fehler = str(fehler)
            return False

    def trennen(self) -> None:
        if self.anschluss is not None:
            try:
                self.anschluss.close()
            except Exception:
                pass
        self.anschluss = None

    def schreiben(self, befehl: str) -> None:
        if not self.verbunden:
            raise RuntimeError("Arduino ist nicht verbunden.")
        daten = f"{befehl.strip()}\n".encode("utf-8")
        self.anschluss.write(daten)
        self.anschluss.flush()

    def zeile_lesen(self) -> str | None:
        if not self.verbunden:
            return None
        roh = self.anschluss.readline()
        if not roh:
            return None
        return roh.decode("utf-8", errors="replace").strip()
