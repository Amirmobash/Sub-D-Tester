from __future__ import annotations

import random
from collections.abc import Iterator

from .config import WIRE_COUNT
from .protocol import Testergebnis


class KabelSimulator:
    def __init__(self, seed: int = 2026) -> None:
        self.seed = seed

    def pruefe_ader(self, ader: int) -> Testergebnis:
        zufall = random.Random(self.seed + ader * 997)
        wert = zufall.random()

        if wert < 0.82:
            return Testergebnis(ader, "ok", ader, (ader,), "Ader ist korrekt verbunden.")

        if wert < 0.90:
            return Testergebnis(ader, "unterbrochen", None, tuple(), "Keine Verbindung erkannt.")

        if wert < 0.97:
            ziel = 1 + ((ader + 2) % WIRE_COUNT)
            return Testergebnis(ader, "vertauscht", ziel, (ziel,), "Ader liegt auf einem anderen Kontakt.")

        ziel = 1 + (ader % WIRE_COUNT)
        return Testergebnis(ader, "kurzschluss", None, tuple(sorted({ader, ziel})), "Mehrere Kontakte reagieren gleichzeitig.")

    def gesamttest(self) -> Iterator[Testergebnis]:
        for ader in range(1, WIRE_COUNT + 1):
            yield self.pruefe_ader(ader)
