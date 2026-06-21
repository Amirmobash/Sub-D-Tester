from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .config import STATUS_ORDER, WIRE_COUNT


class ProtokollFehler(ValueError):
    pass


@dataclass(frozen=True)
class Testergebnis:
    ader: int
    status: str
    ziel: int | None
    treffer: tuple[int, ...]
    meldung: str = ""

    @property
    def ist_fehlerfrei(self) -> bool:
        return self.status == "ok"

    @classmethod
    def aus_dict(cls, daten: dict[str, Any]) -> "Testergebnis":
        nummer = daten.get("pin", daten.get("ader"))
        if nummer is None:
            raise ProtokollFehler("Die Antwort enthält keine Adernummer.")

        try:
            ader = int(nummer)
        except (TypeError, ValueError) as exc:
            raise ProtokollFehler("Die Adernummer ist ungültig.") from exc

        if not 1 <= ader <= WIRE_COUNT:
            raise ProtokollFehler(f"Ader {ader} liegt außerhalb des gültigen Bereichs.")

        status = str(daten.get("status", "fehler")).strip().lower() or "fehler"
        ziel_roh = daten.get("ziel")
        ziel = None if ziel_roh in (None, "", 0, "0") else int(ziel_roh)

        treffer_roh = daten.get("treffer", [])
        if treffer_roh is None:
            treffer = tuple()
        elif isinstance(treffer_roh, list):
            treffer = tuple(int(wert) for wert in treffer_roh)
        else:
            raise ProtokollFehler("Das Feld 'treffer' muss eine Liste sein.")

        meldung = str(daten.get("meldung", "")).strip()
        return cls(ader=ader, status=status, ziel=ziel, treffer=treffer, meldung=meldung)

    @classmethod
    def aus_json(cls, zeile: str) -> "Testergebnis | None":
        text = zeile.strip()
        if not text:
            return None

        try:
            daten = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProtokollFehler(f"Keine gültige JSON-Antwort: {text}") from exc

        if not isinstance(daten, dict):
            raise ProtokollFehler("Die JSON-Antwort ist kein Objekt.")

        typ = daten.get("typ")
        if typ in {"bereit", "start", "ende", "status", "format", "info", "hilfe"}:
            return None

        if typ == "fehler":
            return cls(ader=1, status="fehler", ziel=None, treffer=tuple(), meldung=str(daten.get("meldung", "Arduino meldet einen Fehler.")))

        if typ == "pin" or "pin" in daten or "ader" in daten:
            return cls.aus_dict(daten)

        return None

    def als_dict(self) -> dict[str, Any]:
        return {
            "ader": self.ader,
            "status": self.status,
            "ziel": self.ziel,
            "treffer": list(self.treffer),
            "meldung": self.meldung,
        }


def zaehle_ergebnisse(ergebnisse: dict[int, Testergebnis]) -> dict[str, int]:
    zaehler = {status: 0 for status in STATUS_ORDER}
    for ergebnis in ergebnisse.values():
        zaehler[ergebnis.status if ergebnis.status in zaehler else "fehler"] += 1
    return zaehler


def befehl_fuer_ader(ader: int) -> str:
    if not 1 <= int(ader) <= WIRE_COUNT:
        raise ValueError(f"Ader {ader} ist nicht gültig.")
    return f"PIN {int(ader)}"
