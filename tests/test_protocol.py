from __future__ import annotations

import unittest

from sub_d_tester.config import WIRE_COUNT
from sub_d_tester.protocol import ProtokollFehler, Testergebnis, befehl_fuer_ader, zaehle_ergebnisse
from sub_d_tester.simulator import KabelSimulator


class ProtocolTests(unittest.TestCase):
    def test_pin_json_wird_gelesen(self) -> None:
        zeile = '{"typ":"pin","pin":5,"status":"ok","ziel":5,"treffer":[5],"meldung":"Ader ist korrekt verbunden"}'
        ergebnis = Testergebnis.aus_json(zeile)
        self.assertIsNotNone(ergebnis)
        assert ergebnis is not None
        self.assertEqual(ergebnis.ader, 5)
        self.assertEqual(ergebnis.status, "ok")
        self.assertEqual(ergebnis.ziel, 5)
        self.assertEqual(ergebnis.treffer, (5,))

    def test_status_json_wird_ignoriert(self) -> None:
        self.assertIsNone(Testergebnis.aus_json('{"typ":"status","bereit":true,"adern":25}'))

    def test_ungueltige_ader_wird_abgelehnt(self) -> None:
        with self.assertRaises(ProtokollFehler):
            Testergebnis.aus_json('{"typ":"pin","pin":99,"status":"ok","treffer":[99]}')

    def test_befehl_fuer_ader(self) -> None:
        self.assertEqual(befehl_fuer_ader(7), "PIN 7")
        with self.assertRaises(ValueError):
            befehl_fuer_ader(0)

    def test_simulator_liefert_25_ergebnisse(self) -> None:
        simulator = KabelSimulator(seed=1)
        ergebnisse = list(simulator.gesamttest())
        self.assertEqual(len(ergebnisse), WIRE_COUNT)
        self.assertEqual(ergebnisse[0].ader, 1)
        self.assertEqual(ergebnisse[-1].ader, WIRE_COUNT)

    def test_zaehler(self) -> None:
        daten = {
            1: Testergebnis(1, "ok", 1, (1,), ""),
            2: Testergebnis(2, "kurzschluss", None, (2, 3), ""),
        }
        zaehler = zaehle_ergebnisse(daten)
        self.assertEqual(zaehler["ok"], 1)
        self.assertEqual(zaehler["kurzschluss"], 1)


if __name__ == "__main__":
    unittest.main()
