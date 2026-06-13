from __future__ import annotations

import argparse
import json
import queue
import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

import customtkinter as ctk

try:
    import serial
except ModuleNotFoundError:
    serial = None


ADER_ANZAHL = 25

STATUS_FARBEN = {
    "nicht_geprueft": "#E5E7EB",
    "ok": "#DCFCE7",
    "unterbrochen": "#FEE2E2",
    "vertauscht": "#FEF3C7",
    "kurzschluss": "#FFE4E6",
    "fehler": "#F3E8FF",
    "aktiv": "#DBEAFE",
}

TEXT_FARBEN = {
    "nicht_geprueft": "#475569",
    "ok": "#166534",
    "unterbrochen": "#991B1B",
    "vertauscht": "#92400E",
    "kurzschluss": "#9F1239",
    "fehler": "#6B21A8",
    "aktiv": "#1D4ED8",
}

STATUS_TEXTE = {
    "nicht_geprueft": "Nicht geprüft",
    "ok": "In Ordnung",
    "unterbrochen": "Unterbrochen",
    "vertauscht": "Vertauscht",
    "kurzschluss": "Kurzschluss",
    "fehler": "Fehler",
    "aktiv": "Wird geprüft",
}


@dataclass(frozen=True)
class Testergebnis:
    ader: int
    status: str
    ziel: Optional[int]
    treffer: tuple[int, ...]
    meldung: str

    @classmethod
    def aus_json(cls, daten: dict[str, Any]) -> "Testergebnis":
        ader = int(daten.get("pin", daten.get("ader", 0)))
        status = str(daten.get("status", "fehler"))
        zielwert = daten.get("ziel")
        ziel = int(zielwert) if zielwert not in (None, 0, "0", "") else None
        treffer_roh = daten.get("treffer", [])
        if isinstance(treffer_roh, list):
            treffer = tuple(int(wert) for wert in treffer_roh)
        else:
            treffer = tuple()
        meldung = str(daten.get("meldung", ""))
        return cls(ader=ader, status=status, ziel=ziel, treffer=treffer, meldung=meldung)


class SerielleVerbindung:
    def __init__(self, port: str, baudrate: int) -> None:
        self.port = port
        self.baudrate = baudrate
        self.anschluss: Any = None
        self.letzter_fehler = ""

    @property
    def verbunden(self) -> bool:
        return self.anschluss is not None and bool(getattr(self.anschluss, "is_open", False))

    def verbinden(self) -> bool:
        self.trennen()
        if serial is None:
            self.letzter_fehler = "pyserial ist nicht installiert"
            return False
        try:
            self.anschluss = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
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
            raise RuntimeError("Arduino ist nicht verbunden")
        daten = f"{befehl.strip()}\n".encode("utf-8")
        self.anschluss.write(daten)
        self.anschluss.flush()

    def zeile_lesen(self) -> Optional[str]:
        if not self.verbunden:
            return None
        roh = self.anschluss.readline()
        if not roh:
            return None
        return roh.decode("utf-8", errors="replace").strip()


class AderKarte(ctk.CTkFrame):
    def __init__(self, master: Any, nummer: int) -> None:
        super().__init__(master, corner_radius=16, border_width=1, border_color="#CBD5E1", fg_color="#FFFFFF")
        self.nummer = nummer
        self.grid_columnconfigure(0, weight=1)
        self.kopf = ctk.CTkLabel(
            self,
            text=f"Ader {nummer:02d}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#0F172A",
        )
        self.kopf.grid(row=0, column=0, sticky="ew", padx=10, pady=(12, 2))
        self.status = ctk.CTkLabel(
            self,
            text=STATUS_TEXTE["nicht_geprueft"],
            height=30,
            corner_radius=12,
            fg_color=STATUS_FARBEN["nicht_geprueft"],
            text_color=TEXT_FARBEN["nicht_geprueft"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.status.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        self.details = ctk.CTkLabel(
            self,
            text="Ziel: -",
            font=ctk.CTkFont(size=12),
            text_color="#64748B",
        )
        self.details.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 12))

    def setzen(self, ergebnis: Optional[Testergebnis], status: Optional[str] = None) -> None:
        if ergebnis is None:
            zustand = status or "nicht_geprueft"
            self.status.configure(
                text=STATUS_TEXTE.get(zustand, zustand),
                fg_color=STATUS_FARBEN.get(zustand, STATUS_FARBEN["fehler"]),
                text_color=TEXT_FARBEN.get(zustand, TEXT_FARBEN["fehler"]),
            )
            self.details.configure(text="Ziel: -")
            return

        zustand = ergebnis.status if ergebnis.status in STATUS_TEXTE else "fehler"
        ziel = str(ergebnis.ziel) if ergebnis.ziel is not None else "-"
        treffer = ", ".join(str(wert) for wert in ergebnis.treffer) if ergebnis.treffer else "-"
        self.status.configure(
            text=STATUS_TEXTE[zustand],
            fg_color=STATUS_FARBEN[zustand],
            text_color=TEXT_FARBEN[zustand],
        )
        self.details.configure(text=f"Ziel: {ziel} · Treffer: {treffer}")


class KabeltestAnwendung(ctk.CTk):
    def __init__(self, port: str, baudrate: int, fenster: bool, simulation: bool) -> None:
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.port_var = ctk.StringVar(value=port)
        self.baudrate_var = ctk.StringVar(value=str(baudrate))
        self.simulation_var = ctk.BooleanVar(value=simulation)
        self.einzel_ader_var = ctk.StringVar(value="1")
        self.seriell = SerielleVerbindung(port, baudrate)
        self.warteschlange: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.test_laeuft = False
        self.karten: dict[int, AderKarte] = {}
        self.ergebnisse: dict[int, Testergebnis] = {}
        self.title("Kabeltest")
        self.geometry("1280x820")
        self.minsize(1100, 720)
        self.configure(fg_color="#F4F7FB")
        self.attributes("-fullscreen", not fenster)
        self.bind("<Escape>", lambda event: self.attributes("-fullscreen", False))
        self.bind("<F11>", lambda event: self.attributes("-fullscreen", not bool(self.attributes("-fullscreen"))))
        self.protocol("WM_DELETE_WINDOW", self.schliessen)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.oberflaeche_erstellen()
        self.nachrichten_verarbeiten()

    def oberflaeche_erstellen(self) -> None:
        self.kopfbereich_erstellen()
        self.inhalt_erstellen()
        self.statusleiste_erstellen()

    def kopfbereich_erstellen(self) -> None:
        kopf = ctk.CTkFrame(self, height=102, corner_radius=0, fg_color="#FFFFFF")
        kopf.grid(row=0, column=0, sticky="ew")
        kopf.grid_columnconfigure(1, weight=1)

        titelbereich = ctk.CTkFrame(kopf, fg_color="transparent")
        titelbereich.grid(row=0, column=0, padx=28, pady=18, sticky="w")

        ctk.CTkLabel(
            titelbereich,
            text="Kabeltest",
            font=ctk.CTkFont(family="Arial Black", size=30),
            text_color="#0F172A",
        ).pack(anchor="w")

        ctk.CTkLabel(
            titelbereich,
            text="Prüfoberfläche für D-Sub-25 Leitungen mit Arduino Mega",
            font=ctk.CTkFont(size=13),
            text_color="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        verbindung = ctk.CTkFrame(kopf, fg_color="transparent")
        verbindung.grid(row=0, column=1, sticky="ew", padx=20, pady=18)
        verbindung.grid_columnconfigure(0, weight=1)
        verbindung.grid_columnconfigure(1, weight=1)

        self.port_eingabe = ctk.CTkEntry(verbindung, textvariable=self.port_var, placeholder_text="Port", height=40)
        self.port_eingabe.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.baudrate_eingabe = ctk.CTkEntry(verbindung, textvariable=self.baudrate_var, placeholder_text="Baudrate", height=40)
        self.baudrate_eingabe.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.simulation_schalter = ctk.CTkSwitch(verbindung, text="Simulation", variable=self.simulation_var)
        self.simulation_schalter.grid(row=0, column=2, padx=(2, 0))

        aktionen = ctk.CTkFrame(kopf, fg_color="transparent")
        aktionen.grid(row=0, column=2, padx=28, pady=18, sticky="e")

        self.verbindungs_label = ctk.CTkLabel(
            aktionen,
            text="Nicht verbunden",
            width=170,
            height=32,
            corner_radius=16,
            fg_color="#FEE2E2",
            text_color="#991B1B",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.verbindungs_label.pack(anchor="e", pady=(0, 8))

        zeile = ctk.CTkFrame(aktionen, fg_color="transparent")
        zeile.pack(anchor="e")

        self.verbinden_knopf = ctk.CTkButton(zeile, text="Verbinden", width=100, height=34, command=self.verbinden)
        self.verbinden_knopf.grid(row=0, column=0, padx=(0, 8))

        self.trennen_knopf = ctk.CTkButton(
            zeile,
            text="Trennen",
            width=90,
            height=34,
            fg_color="#64748B",
            hover_color="#475569",
            command=self.trennen,
        )
        self.trennen_knopf.grid(row=0, column=1)

    def inhalt_erstellen(self) -> None:
        inhalt = ctk.CTkFrame(self, fg_color="transparent")
        inhalt.grid(row=1, column=0, sticky="nsew", padx=24, pady=22)
        inhalt.grid_columnconfigure(0, weight=3)
        inhalt.grid_columnconfigure(1, weight=1)
        inhalt.grid_rowconfigure(0, weight=1)

        links = ctk.CTkFrame(inhalt, fg_color="#FFFFFF", corner_radius=22)
        links.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        links.grid_columnconfigure(0, weight=1)
        links.grid_rowconfigure(1, weight=1)

        steuerung = ctk.CTkFrame(links, fg_color="transparent")
        steuerung.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 8))
        steuerung.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(
            steuerung,
            text="Adernübersicht",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#0F172A",
        ).grid(row=0, column=0, sticky="w", padx=(0, 14))

        self.gesamttest_knopf = ctk.CTkButton(steuerung, text="Gesamttest starten", height=38, command=self.gesamttest_starten)
        self.gesamttest_knopf.grid(row=0, column=1, padx=(0, 10))

        self.einzel_ader = ctk.CTkOptionMenu(steuerung, values=[str(i) for i in range(1, ADER_ANZAHL + 1)], variable=self.einzel_ader_var, width=82, height=38)
        self.einzel_ader.grid(row=0, column=2, padx=(0, 10))

        self.einzeltest_knopf = ctk.CTkButton(steuerung, text="Einzeltest", width=110, height=38, command=self.einzeltest_starten)
        self.einzeltest_knopf.grid(row=0, column=3, padx=(0, 10))

        self.zuruecksetzen_knopf = ctk.CTkButton(
            steuerung,
            text="Zurücksetzen",
            width=120,
            height=38,
            fg_color="#64748B",
            hover_color="#475569",
            command=self.zuruecksetzen,
        )
        self.zuruecksetzen_knopf.grid(row=0, column=5, sticky="e")

        raster = ctk.CTkScrollableFrame(links, fg_color="transparent")
        raster.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 16))

        for spalte in range(5):
            raster.grid_columnconfigure(spalte, weight=1)

        for nummer in range(1, ADER_ANZAHL + 1):
            karte = AderKarte(raster, nummer)
            karte.grid(row=(nummer - 1) // 5, column=(nummer - 1) % 5, sticky="nsew", padx=10, pady=10)
            self.karten[nummer] = karte

        rechts = ctk.CTkFrame(inhalt, fg_color="#FFFFFF", corner_radius=22)
        rechts.grid(row=0, column=1, sticky="nsew")
        rechts.grid_columnconfigure(0, weight=1)
        rechts.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(
            rechts,
            text="Prüfstatus",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#0F172A",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 12))

        self.fortschritt = ctk.CTkProgressBar(rechts, height=14, corner_radius=8)
        self.fortschritt.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 18))
        self.fortschritt.set(0)

        self.zusammenfassung = ctk.CTkLabel(
            rechts,
            text="Noch kein Test gestartet.",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#334155",
            wraplength=310,
            justify="left",
        )
        self.zusammenfassung.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 14))

        self.statistik = ctk.CTkLabel(
            rechts,
            text="OK: 0\nUnterbrochen: 0\nVertauscht: 0\nKurzschluss: 0\nFehler: 0",
            font=ctk.CTkFont(size=14),
            text_color="#475569",
            justify="left",
        )
        self.statistik.grid(row=3, column=0, sticky="w", padx=24, pady=(0, 18))

        ctk.CTkLabel(
            rechts,
            text="Protokoll",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#0F172A",
        ).grid(row=4, column=0, sticky="w", padx=24, pady=(0, 8))

        self.protokoll = ctk.CTkTextbox(rechts, height=260, corner_radius=14, border_width=1, border_color="#E2E8F0")
        self.protokoll.grid(row=5, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.protokoll.configure(state="disabled")

    def statusleiste_erstellen(self) -> None:
        leiste = ctk.CTkFrame(self, height=42, corner_radius=0, fg_color="#FFFFFF")
        leiste.grid(row=2, column=0, sticky="ew")
        leiste.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            leiste,
            text="Bereit · ESC beendet Vollbild · F11 wechselt Vollbild",
            font=ctk.CTkFont(size=12),
            text_color="#64748B",
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=24)

    def verbinden(self) -> None:
        if self.test_laeuft:
            return
        try:
            baudrate = int(self.baudrate_var.get().strip())
        except ValueError:
            self.protokoll_schreiben("Ungültige Baudrate.")
            return
        self.seriell = SerielleVerbindung(self.port_var.get().strip(), baudrate)
        self.verbindungs_label.configure(text="Verbinde...", fg_color="#FEF3C7", text_color="#92400E")
        self.update_idletasks()
        if self.seriell.verbinden():
            self.verbindungs_label.configure(text="Verbunden", fg_color="#DCFCE7", text_color="#166534")
            self.protokoll_schreiben(f"Verbunden mit {self.seriell.port} bei {self.seriell.baudrate} Baud.")
        else:
            self.verbindungs_label.configure(text="Nicht verbunden", fg_color="#FEE2E2", text_color="#991B1B")
            self.protokoll_schreiben(f"Verbindung fehlgeschlagen: {self.seriell.letzter_fehler}")

    def trennen(self) -> None:
        self.seriell.trennen()
        self.verbindungs_label.configure(text="Nicht verbunden", fg_color="#FEE2E2", text_color="#991B1B")
        self.protokoll_schreiben("Verbindung getrennt.")

    def gesamttest_starten(self) -> None:
        if self.test_laeuft:
            return
        self.zuruecksetzen()
        self.test_laeuft = True
        self.schaltflaechen_setzen(False)
        threading.Thread(target=self.gesamttest_worker, daemon=True).start()

    def einzeltest_starten(self) -> None:
        if self.test_laeuft:
            return
        try:
            ader = int(self.einzel_ader_var.get())
        except ValueError:
            return
        self.test_laeuft = True
        self.schaltflaechen_setzen(False)
        self.karten[ader].setzen(None, "aktiv")
        threading.Thread(target=self.einzeltest_worker, args=(ader,), daemon=True).start()

    def gesamttest_worker(self) -> None:
        try:
            if self.simulation_var.get() or not self.seriell.verbunden:
                self.simulierter_gesamttest()
            else:
                self.serieller_gesamttest()
        except Exception as fehler:
            self.warteschlange.put(("log", f"Fehler im Testlauf: {fehler}"))
        finally:
            self.warteschlange.put(("fertig", None))

    def einzeltest_worker(self, ader: int) -> None:
        try:
            if self.simulation_var.get() or not self.seriell.verbunden:
                time.sleep(0.3)
                ergebnis = self.simuliertes_ergebnis(ader)
                self.warteschlange.put(("ergebnis", ergebnis))
            else:
                self.seriell.schreiben("FORMAT JSON")
                self.seriell.schreiben(f"PIN {ader}")
                ende = time.monotonic() + 8
                while time.monotonic() < ende:
                    zeile = self.seriell.zeile_lesen()
                    if not zeile:
                        continue
                    daten = json.loads(zeile)
                    if daten.get("typ") == "pin" or "pin" in daten:
                        self.warteschlange.put(("ergebnis", Testergebnis.aus_json(daten)))
                        return
                self.warteschlange.put(("log", "Keine Antwort vom Arduino erhalten."))
        except Exception as fehler:
            self.warteschlange.put(("log", f"Einzeltest fehlgeschlagen: {fehler}"))
        finally:
            self.warteschlange.put(("fertig", None))

    def serieller_gesamttest(self) -> None:
        self.warteschlange.put(("log", "Gesamttest über Arduino gestartet."))
        self.seriell.schreiben("FORMAT JSON")
        self.seriell.schreiben("TEST")
        ende = time.monotonic() + 45
        while time.monotonic() < ende:
            zeile = self.seriell.zeile_lesen()
            if not zeile:
                continue
            daten = json.loads(zeile)
            typ = daten.get("typ")
            if typ == "ende":
                self.warteschlange.put(("log", "Arduino meldet Testende."))
                return
            if typ == "pin" or "pin" in daten:
                self.warteschlange.put(("ergebnis", Testergebnis.aus_json(daten)))
        self.warteschlange.put(("log", "Zeitlimit erreicht. Test wurde beendet."))

    def simulierter_gesamttest(self) -> None:
        self.warteschlange.put(("log", "Simulation gestartet."))
        for ader in range(1, ADER_ANZAHL + 1):
            self.warteschlange.put(("aktiv", ader))
            time.sleep(0.08)
            self.warteschlange.put(("ergebnis", self.simuliertes_ergebnis(ader)))
        self.warteschlange.put(("log", "Simulation beendet."))

    def simuliertes_ergebnis(self, ader: int) -> Testergebnis:
        zufall = random.Random(ader * 991)
        wert = zufall.random()
        if wert < 0.82:
            return Testergebnis(ader, "ok", ader, (ader,), "Ader ist korrekt verbunden")
        if wert < 0.89:
            return Testergebnis(ader, "unterbrochen", None, tuple(), "Keine Verbindung erkannt")
        if wert < 0.96:
            ziel = 1 + ((ader + 2) % ADER_ANZAHL)
            return Testergebnis(ader, "vertauscht", ziel, (ziel,), "Ader liegt auf einem anderen Kontakt")
        ziel = 1 + (ader % ADER_ANZAHL)
        return Testergebnis(ader, "kurzschluss", None, (ader, ziel), "Mehrere Kontakte reagieren gleichzeitig")

    def nachrichten_verarbeiten(self) -> None:
        try:
            while True:
                typ, inhalt = self.warteschlange.get_nowait()
                if typ == "log":
                    self.protokoll_schreiben(str(inhalt))
                elif typ == "aktiv":
                    ader = int(inhalt)
                    self.karten[ader].setzen(None, "aktiv")
                    self.status_label.configure(text=f"Prüfe Ader {ader} von {ADER_ANZAHL}")
                elif typ == "ergebnis":
                    self.ergebnis_eintragen(inhalt)
                elif typ == "fertig":
                    self.test_laeuft = False
                    self.schaltflaechen_setzen(True)
                    self.zusammenfassung_aktualisieren()
                    self.status_label.configure(text="Bereit · ESC beendet Vollbild · F11 wechselt Vollbild")
        except queue.Empty:
            pass
        self.after(80, self.nachrichten_verarbeiten)

    def ergebnis_eintragen(self, ergebnis: Testergebnis) -> None:
        if ergebnis.ader in self.karten:
            self.ergebnisse[ergebnis.ader] = ergebnis
            self.karten[ergebnis.ader].setzen(ergebnis)
            text = f"Ader {ergebnis.ader:02d}: {STATUS_TEXTE.get(ergebnis.status, ergebnis.status)}"
            if ergebnis.meldung:
                text += f" · {ergebnis.meldung}"
            self.protokoll_schreiben(text)
            self.fortschritt.set(len(self.ergebnisse) / ADER_ANZAHL)
            self.zusammenfassung_aktualisieren()

    def zusammenfassung_aktualisieren(self) -> None:
        zaehler = {"ok": 0, "unterbrochen": 0, "vertauscht": 0, "kurzschluss": 0, "fehler": 0}
        for ergebnis in self.ergebnisse.values():
            if ergebnis.status in zaehler:
                zaehler[ergebnis.status] += 1
            else:
                zaehler["fehler"] += 1
        geprueft = len(self.ergebnisse)
        self.zusammenfassung.configure(text=f"{geprueft} von {ADER_ANZAHL} Adern geprüft.")
        self.statistik.configure(
            text=(
                f"OK: {zaehler['ok']}\n"
                f"Unterbrochen: {zaehler['unterbrochen']}\n"
                f"Vertauscht: {zaehler['vertauscht']}\n"
                f"Kurzschluss: {zaehler['kurzschluss']}\n"
                f"Fehler: {zaehler['fehler']}"
            )
        )

    def protokoll_schreiben(self, text: str) -> None:
        zeit = time.strftime("%H:%M:%S")
        self.protokoll.configure(state="normal")
        self.protokoll.insert("end", f"[{zeit}] {text}\n")
        self.protokoll.see("end")
        self.protokoll.configure(state="disabled")

    def zuruecksetzen(self) -> None:
        self.ergebnisse.clear()
        for karte in self.karten.values():
            karte.setzen(None)
        self.fortschritt.set(0)
        self.zusammenfassung.configure(text="Noch kein Test gestartet.")
        self.statistik.configure(text="OK: 0\nUnterbrochen: 0\nVertauscht: 0\nKurzschluss: 0\nFehler: 0")
        self.protokoll_schreiben("Anzeige zurückgesetzt.")

    def schaltflaechen_setzen(self, aktiv: bool) -> None:
        zustand = "normal" if aktiv else "disabled"
        self.gesamttest_knopf.configure(state=zustand)
        self.einzeltest_knopf.configure(state=zustand)
        self.zuruecksetzen_knopf.configure(state=zustand)
        self.verbinden_knopf.configure(state=zustand)
        self.trennen_knopf.configure(state=zustand)

    def schliessen(self) -> None:
        self.seriell.trennen()
        self.destroy()


def argumente_lesen() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="Kabeltest")
    parser.add_argument("--port", default="COM9")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--fenster", action="store_true")
    parser.add_argument("--simulation", action="store_true")
    return parser.parse_args()


def main() -> None:
    argumente = argumente_lesen()
    anwendung = KabeltestAnwendung(
        port=argumente.port,
        baudrate=argumente.baudrate,
        fenster=argumente.fenster,
        simulation=argumente.simulation,
    )
    anwendung.mainloop()


if __name__ == "__main__":
    main()
