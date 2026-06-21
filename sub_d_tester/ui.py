from __future__ import annotations

import csv
import queue
import threading
import time
from pathlib import Path
from typing import Any

import customtkinter as ctk

from .config import APP_NAME, AUTHOR, DEFAULT_BAUDRATE, STATUS_COLORS, STATUS_LABELS, STATUS_ORDER, VERSION, WIRE_COUNT
from .protocol import ProtokollFehler, Testergebnis, befehl_fuer_ader, zaehle_ergebnisse
from .serial_connection import SerielleVerbindung
from .simulator import KabelSimulator


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
            text=STATUS_LABELS["nicht_geprueft"],
            height=30,
            corner_radius=12,
            fg_color=STATUS_COLORS["nicht_geprueft"][0],
            text_color=STATUS_COLORS["nicht_geprueft"][1],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.status.grid(row=1, column=0, sticky="ew", padx=10, pady=8)

        self.details = ctk.CTkLabel(self, text="Ziel: –", font=ctk.CTkFont(size=12), text_color="#64748B")
        self.details.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 12))

    def aktualisieren(self, ergebnis: Testergebnis | None = None, status: str = "nicht_geprueft") -> None:
        if ergebnis is None:
            hintergrund, textfarbe = STATUS_COLORS.get(status, STATUS_COLORS["fehler"])
            self.status.configure(text=STATUS_LABELS.get(status, status), fg_color=hintergrund, text_color=textfarbe)
            self.details.configure(text="Ziel: –")
            return

        status_name = ergebnis.status if ergebnis.status in STATUS_LABELS else "fehler"
        hintergrund, textfarbe = STATUS_COLORS[status_name]
        ziel = ergebnis.ziel if ergebnis.ziel is not None else "–"
        treffer = ", ".join(str(wert) for wert in ergebnis.treffer) if ergebnis.treffer else "–"
        self.status.configure(text=STATUS_LABELS[status_name], fg_color=hintergrund, text_color=textfarbe)
        self.details.configure(text=f"Ziel: {ziel} · Treffer: {treffer}")


class SubDTesterApp(ctk.CTk):
    def __init__(self, port: str, baudrate: int, fenster: bool, simulation: bool) -> None:
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.port_var = ctk.StringVar(value=port)
        self.baudrate_var = ctk.StringVar(value=str(baudrate))
        self.simulation_var = ctk.BooleanVar(value=simulation)
        self.einzelader_var = ctk.StringVar(value="1")
        self.nachrichten: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.simulator = KabelSimulator()
        self.seriell = SerielleVerbindung(port, baudrate)
        self.karten: dict[int, AderKarte] = {}
        self.ergebnisse: dict[int, Testergebnis] = {}
        self.test_laeuft = False

        self.title(f"{APP_NAME} – D-Sub-25 Kabelprüfung")
        self.geometry("1280x820")
        self.minsize(1080, 700)
        self.configure(fg_color="#F4F7FB")
        self.attributes("-fullscreen", not fenster)
        self.bind("<Escape>", lambda _event: self.attributes("-fullscreen", False))
        self.bind("<F11>", lambda _event: self.attributes("-fullscreen", not bool(self.attributes("-fullscreen"))))
        self.protocol("WM_DELETE_WINDOW", self.schliessen)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.oberflaeche_bauen()
        self.nachrichten_verarbeiten()

    def oberflaeche_bauen(self) -> None:
        self.kopfbereich_bauen()
        self.inhalt_bauen()
        self.statusleiste_bauen()

    def kopfbereich_bauen(self) -> None:
        kopf = ctk.CTkFrame(self, height=110, corner_radius=0, fg_color="#FFFFFF")
        kopf.grid(row=0, column=0, sticky="ew")
        kopf.grid_columnconfigure(1, weight=1)

        titel = ctk.CTkFrame(kopf, fg_color="transparent")
        titel.grid(row=0, column=0, sticky="w", padx=28, pady=18)

        ctk.CTkLabel(
            titel,
            text=APP_NAME,
            font=ctk.CTkFont(family="Arial Black", size=30),
            text_color="#0F172A",
        ).pack(anchor="w")
        ctk.CTkLabel(
            titel,
            text=f"D-Sub-25 Kabelprüfung · {AUTHOR}",
            font=ctk.CTkFont(size=13),
            text_color="#64748B",
        ).pack(anchor="w", pady=(2, 0))

        verbindung = ctk.CTkFrame(kopf, fg_color="transparent")
        verbindung.grid(row=0, column=1, sticky="ew", padx=18, pady=18)
        verbindung.grid_columnconfigure(0, weight=1)
        verbindung.grid_columnconfigure(1, weight=1)

        self.port_eingabe = ctk.CTkEntry(verbindung, textvariable=self.port_var, placeholder_text="Port", height=40)
        self.port_eingabe.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.baudrate_eingabe = ctk.CTkEntry(verbindung, textvariable=self.baudrate_var, placeholder_text="Baudrate", height=40)
        self.baudrate_eingabe.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.simulation_schalter = ctk.CTkSwitch(verbindung, text="Simulation", variable=self.simulation_var)
        self.simulation_schalter.grid(row=0, column=2, padx=(2, 0))

        aktionen = ctk.CTkFrame(kopf, fg_color="transparent")
        aktionen.grid(row=0, column=2, sticky="e", padx=28, pady=18)

        self.verbindungs_label = ctk.CTkLabel(
            aktionen,
            text="Nicht verbunden",
            width=180,
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
        self.trennen_knopf = ctk.CTkButton(zeile, text="Trennen", width=90, height=34, fg_color="#64748B", hover_color="#475569", command=self.trennen)
        self.trennen_knopf.grid(row=0, column=1)

    def inhalt_bauen(self) -> None:
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
        steuerung.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(steuerung, text="Adernübersicht", font=ctk.CTkFont(size=20, weight="bold"), text_color="#0F172A").grid(row=0, column=0, sticky="w", padx=(0, 14))
        self.gesamttest_knopf = ctk.CTkButton(steuerung, text="Gesamttest starten", height=38, command=self.gesamttest_starten)
        self.gesamttest_knopf.grid(row=0, column=1, padx=(0, 10))
        self.einzelader_menu = ctk.CTkOptionMenu(steuerung, values=[str(i) for i in range(1, WIRE_COUNT + 1)], variable=self.einzelader_var, width=82, height=38)
        self.einzelader_menu.grid(row=0, column=2, padx=(0, 10))
        self.einzeltest_knopf = ctk.CTkButton(steuerung, text="Einzeltest", width=110, height=38, command=self.einzeltest_starten)
        self.einzeltest_knopf.grid(row=0, column=3, padx=(0, 10))
        self.csv_knopf = ctk.CTkButton(steuerung, text="CSV speichern", width=120, height=38, command=self.csv_speichern)
        self.csv_knopf.grid(row=0, column=4, padx=(0, 10))
        self.zuruecksetzen_knopf = ctk.CTkButton(steuerung, text="Zurücksetzen", width=120, height=38, fg_color="#64748B", hover_color="#475569", command=self.zuruecksetzen)
        self.zuruecksetzen_knopf.grid(row=0, column=6, sticky="e")

        raster = ctk.CTkScrollableFrame(links, fg_color="transparent")
        raster.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 16))
        for spalte in range(5):
            raster.grid_columnconfigure(spalte, weight=1)
        for nummer in range(1, WIRE_COUNT + 1):
            karte = AderKarte(raster, nummer)
            karte.grid(row=(nummer - 1) // 5, column=(nummer - 1) % 5, sticky="nsew", padx=10, pady=10)
            self.karten[nummer] = karte

        rechts = ctk.CTkFrame(inhalt, fg_color="#FFFFFF", corner_radius=22)
        rechts.grid(row=0, column=1, sticky="nsew")
        rechts.grid_columnconfigure(0, weight=1)
        rechts.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(rechts, text="Prüfstatus", font=ctk.CTkFont(size=22, weight="bold"), text_color="#0F172A").grid(row=0, column=0, sticky="w", padx=24, pady=(24, 12))
        self.fortschritt = ctk.CTkProgressBar(rechts, height=14, corner_radius=8)
        self.fortschritt.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 18))
        self.fortschritt.set(0)
        self.zusammenfassung = ctk.CTkLabel(rechts, text="Noch kein Test gestartet.", font=ctk.CTkFont(size=15, weight="bold"), text_color="#334155", wraplength=310, justify="left")
        self.zusammenfassung.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 14))
        self.statistik = ctk.CTkLabel(rechts, text=self.statistik_text({status: 0 for status in STATUS_ORDER}), font=ctk.CTkFont(size=14), text_color="#475569", justify="left")
        self.statistik.grid(row=3, column=0, sticky="w", padx=24, pady=(0, 18))
        ctk.CTkLabel(rechts, text="Protokoll", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0F172A").grid(row=4, column=0, sticky="w", padx=24, pady=(0, 8))
        self.protokoll = ctk.CTkTextbox(rechts, height=260, corner_radius=14, border_width=1, border_color="#E2E8F0")
        self.protokoll.grid(row=5, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.protokoll.configure(state="disabled")

    def statusleiste_bauen(self) -> None:
        leiste = ctk.CTkFrame(self, height=42, corner_radius=0, fg_color="#FFFFFF")
        leiste.grid(row=2, column=0, sticky="ew")
        leiste.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(leiste, text=f"Bereit · {APP_NAME} {VERSION} · ESC beendet Vollbild · F11 wechselt Vollbild", font=ctk.CTkFont(size=12), text_color="#64748B")
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
        self.zuruecksetzen(loggen=False)
        self.test_laeuft = True
        self.schaltflaechen_setzen(False)
        threading.Thread(target=self.gesamttest_worker, daemon=True).start()

    def einzeltest_starten(self) -> None:
        if self.test_laeuft:
            return
        ader = int(self.einzelader_var.get())
        self.test_laeuft = True
        self.schaltflaechen_setzen(False)
        self.karten[ader].aktualisieren(status="aktiv")
        threading.Thread(target=self.einzeltest_worker, args=(ader,), daemon=True).start()

    def gesamttest_worker(self) -> None:
        try:
            if self.simulation_var.get() or not self.seriell.verbunden:
                self.nachrichten.put(("log", "Simulation gestartet."))
                for ergebnis in self.simulator.gesamttest():
                    self.nachrichten.put(("aktiv", ergebnis.ader))
                    time.sleep(0.08)
                    self.nachrichten.put(("ergebnis", ergebnis))
                self.nachrichten.put(("log", "Simulation beendet."))
            else:
                self.seriell.schreiben("FORMAT JSON")
                self.seriell.schreiben("TEST")
                ende = time.monotonic() + 45
                while time.monotonic() < ende:
                    zeile = self.seriell.zeile_lesen()
                    if not zeile:
                        continue
                    try:
                        ergebnis = Testergebnis.aus_json(zeile)
                    except ProtokollFehler as fehler:
                        self.nachrichten.put(("log", str(fehler)))
                        continue
                    if ergebnis is not None:
                        self.nachrichten.put(("ergebnis", ergebnis))
                    if "\"typ\":\"ende\"" in zeile.replace(" ", ""):
                        break
        except Exception as fehler:
            self.nachrichten.put(("log", f"Testlauf fehlgeschlagen: {fehler}"))
        finally:
            self.nachrichten.put(("fertig", None))

    def einzeltest_worker(self, ader: int) -> None:
        try:
            if self.simulation_var.get() or not self.seriell.verbunden:
                time.sleep(0.25)
                self.nachrichten.put(("ergebnis", self.simulator.pruefe_ader(ader)))
            else:
                self.seriell.schreiben("FORMAT JSON")
                self.seriell.schreiben(befehl_fuer_ader(ader))
                ende = time.monotonic() + 8
                while time.monotonic() < ende:
                    zeile = self.seriell.zeile_lesen()
                    if not zeile:
                        continue
                    ergebnis = Testergebnis.aus_json(zeile)
                    if ergebnis is not None:
                        self.nachrichten.put(("ergebnis", ergebnis))
                        return
                self.nachrichten.put(("log", "Keine Antwort vom Arduino erhalten."))
        except Exception as fehler:
            self.nachrichten.put(("log", f"Einzeltest fehlgeschlagen: {fehler}"))
        finally:
            self.nachrichten.put(("fertig", None))

    def nachrichten_verarbeiten(self) -> None:
        try:
            while True:
                typ, inhalt = self.nachrichten.get_nowait()
                if typ == "log":
                    self.protokoll_schreiben(str(inhalt))
                elif typ == "aktiv":
                    ader = int(inhalt)
                    self.karten[ader].aktualisieren(status="aktiv")
                    self.status_label.configure(text=f"Prüfe Ader {ader} von {WIRE_COUNT}")
                elif typ == "ergebnis":
                    self.ergebnis_eintragen(inhalt)
                elif typ == "fertig":
                    self.test_laeuft = False
                    self.schaltflaechen_setzen(True)
                    self.zusammenfassung_aktualisieren()
                    self.status_label.configure(text=f"Bereit · {APP_NAME} {VERSION} · ESC beendet Vollbild · F11 wechselt Vollbild")
        except queue.Empty:
            pass
        self.after(80, self.nachrichten_verarbeiten)

    def ergebnis_eintragen(self, ergebnis: Testergebnis) -> None:
        self.ergebnisse[ergebnis.ader] = ergebnis
        self.karten[ergebnis.ader].aktualisieren(ergebnis)
        text = f"Ader {ergebnis.ader:02d}: {STATUS_LABELS.get(ergebnis.status, ergebnis.status)}"
        if ergebnis.meldung:
            text += f" · {ergebnis.meldung}"
        self.protokoll_schreiben(text)
        self.fortschritt.set(len(self.ergebnisse) / WIRE_COUNT)
        self.zusammenfassung_aktualisieren()

    def zusammenfassung_aktualisieren(self) -> None:
        zaehler = zaehle_ergebnisse(self.ergebnisse)
        geprueft = len(self.ergebnisse)
        if geprueft == 0:
            self.zusammenfassung.configure(text="Noch kein Test gestartet.")
        elif zaehler["ok"] == geprueft and geprueft == WIRE_COUNT:
            self.zusammenfassung.configure(text=f"Alle {WIRE_COUNT} Adern sind in Ordnung.")
        else:
            self.zusammenfassung.configure(text=f"{geprueft} von {WIRE_COUNT} Adern geprüft.")
        self.statistik.configure(text=self.statistik_text(zaehler))

    def statistik_text(self, zaehler: dict[str, int]) -> str:
        return "\n".join(f"{STATUS_LABELS[status]}: {zaehler.get(status, 0)}" for status in STATUS_ORDER)

    def csv_speichern(self) -> None:
        if not self.ergebnisse:
            self.protokoll_schreiben("Noch keine Ergebnisse zum Speichern vorhanden.")
            return
        dateiname = Path.cwd() / f"sub_d_tester_ergebnis_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        with dateiname.open("w", newline="", encoding="utf-8") as datei:
            writer = csv.writer(datei, delimiter=";")
            writer.writerow(["Ader", "Status", "Ziel", "Treffer", "Meldung"])
            for ader in range(1, WIRE_COUNT + 1):
                ergebnis = self.ergebnisse.get(ader)
                if ergebnis is None:
                    writer.writerow([ader, "nicht_geprueft", "", "", ""])
                else:
                    writer.writerow([ergebnis.ader, ergebnis.status, ergebnis.ziel or "", ",".join(map(str, ergebnis.treffer)), ergebnis.meldung])
        self.protokoll_schreiben(f"CSV gespeichert: {dateiname}")

    def protokoll_schreiben(self, text: str) -> None:
        zeit = time.strftime("%H:%M:%S")
        self.protokoll.configure(state="normal")
        self.protokoll.insert("end", f"[{zeit}] {text}\n")
        self.protokoll.see("end")
        self.protokoll.configure(state="disabled")

    def zuruecksetzen(self, loggen: bool = True) -> None:
        self.ergebnisse.clear()
        for karte in self.karten.values():
            karte.aktualisieren()
        self.fortschritt.set(0)
        self.zusammenfassung_aktualisieren()
        if loggen:
            self.protokoll_schreiben("Anzeige zurückgesetzt.")

    def schaltflaechen_setzen(self, aktiv: bool) -> None:
        zustand = "normal" if aktiv else "disabled"
        for knopf in [self.gesamttest_knopf, self.einzeltest_knopf, self.csv_knopf, self.zuruecksetzen_knopf, self.verbinden_knopf, self.trennen_knopf]:
            knopf.configure(state=zustand)

    def schliessen(self) -> None:
        self.seriell.trennen()
        self.destroy()


def starte_app(port: str, baudrate: int = DEFAULT_BAUDRATE, fenster: bool = False, simulation: bool = False) -> None:
    app = SubDTesterApp(port=port, baudrate=baudrate, fenster=fenster, simulation=simulation)
    app.mainloop()
