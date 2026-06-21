# Sub-D-Tester

**Sub-D-Tester** ist ein sauber aufgebautes Werkstattprojekt zum Prüfen von D-Sub-25 Kabeln und kleinen Kabelbäumen. Die Anwendung kombiniert einen Arduino-Mega-Sketch mit einer übersichtlichen Python-Oberfläche. So lassen sich 25 Adern Schritt für Schritt auf Durchgang, Unterbrechung, Vertauschung und Kurzschluss prüfen.

Autor: **Amir Mobahseraghdam**

Das Projekt ist bewusst praktisch gehalten. Es soll in der Werkstatt, im Labor, in der Ausbildung oder beim Aufbau eigener Testadapter schnell verständlich sein. Die Namen im Code sind sprechend gewählt, die Struktur ist klein genug zum Lernen und sauber genug zum Weiterbauen.

## Was kann das Projekt?

- D-Sub-25 Leitungen automatisch prüfen
- Arduino Mega als Mess- und Steuereinheit verwenden
- Python-Desktopoberfläche mit CustomTkinter starten
- Einzelne Adern oder alle 25 Adern testen
- Ergebnisse live als Karten anzeigen
- Status `ok`, `unterbrochen`, `vertauscht`, `kurzschluss` und `fehler` auswerten
- Serielles JSON-Protokoll zwischen Arduino und PC nutzen
- Simulationsmodus ohne Hardware starten
- Prüfergebnisse als CSV speichern
- Vollbildmodus für Werkstatt- oder Touchscreenbetrieb verwenden

## Projektidee

Bei einem 25-poligen Stecker wird ein manueller Kabeltest schnell unübersichtlich. Dieses Projekt nimmt dem Anwender die Wiederholung ab: Der Arduino legt nacheinander jede Ausgangsader auf LOW und liest auf der Gegenseite alle Eingänge. Die Python-Oberfläche zeigt sofort, welche Leitung stimmt und wo nachgearbeitet werden muss.

## Hardware

Empfohlen wird ein Arduino Mega, weil genügend digitale und analoge Pins vorhanden sind.

| Bauteil | Zweck |
|---|---|
| Arduino Mega | Steuerung und Messung der 25 Leitungen |
| 2 × D-Sub-25 Buchse oder Stecker | Anschluss für Prüfling und Gegenstück |
| Klemmen, Adapterplatine oder Shield | Saubere Verdrahtung |
| USB-Kabel | Verbindung zum PC |
| Gehäuse, Frontplatte, Beschriftung | Optional für die Werkstatt |

## Pinbelegung

| Ader | Ausgang | Eingang |
|---:|---:|---:|
| 1 | 22 | A0 |
| 2 | 23 | A1 |
| 3 | 24 | A2 |
| 4 | 25 | A3 |
| 5 | 26 | A4 |
| 6 | 27 | A5 |
| 7 | 28 | A6 |
| 8 | 29 | A7 |
| 9 | 30 | A8 |
| 10 | 31 | A9 |
| 11 | 32 | A10 |
| 12 | 33 | A11 |
| 13 | 34 | A12 |
| 14 | 35 | A13 |
| 15 | 36 | A14 |
| 16 | 37 | A15 |
| 17 | 38 | 2 |
| 18 | 39 | 3 |
| 19 | 40 | 4 |
| 20 | 41 | 5 |
| 21 | 42 | 6 |
| 22 | 43 | 7 |
| 23 | 44 | 8 |
| 24 | 45 | 9 |
| 25 | 46 | 10 |

Die Zuordnung steht im Arduino-Sketch in den Arrays `ausgangspins` und `eingangspins`.

## Installation

### 1. Python-Umgebung vorbereiten

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Dann die Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

### 2. Arduino-Sketch hochladen

Datei öffnen:

```text
arduino/sub_d_tester_mega/sub_d_tester_mega.ino
```

In der Arduino IDE:

1. Board: **Arduino Mega or Mega 2560** wählen
2. Richtigen Port auswählen
3. Sketch kompilieren und hochladen
4. Serial Monitor schließen, bevor die Python-App verbindet

### 3. Python-App starten

Mit Hardware:

```bash
python main.py --port COM7 --fenster
```

Linux-Beispiel:

```bash
python main.py --port /dev/ttyACM0 --fenster
```

Ohne Hardware im Simulationsmodus:

```bash
python main.py --simulation --fenster
```

Vollbildmodus:

```bash
python main.py --simulation
```

`ESC` beendet den Vollbildmodus, `F11` schaltet ihn um.

## Serielle Befehle

Die Kommunikation läuft mit **9600 Baud**. Die Python-App nutzt standardmäßig JSON.

| Befehl | Wirkung |
|---|---|
| `TEST` | Prüft alle 25 Adern |
| `PIN 7` | Prüft nur Ader 7 |
| `STATUS` | Gibt den aktuellen Status zurück |
| `FORMAT JSON` | Aktiviert JSON-Ausgabe |
| `FORMAT TEXT` | Aktiviert Textausgabe für manuelle Tests |
| `RESET` | Setzt alle Pins wieder in den sicheren Grundzustand |
| `HILFE` | Gibt die Befehle aus |

Beispielantwort:

```json
{"typ":"pin","pin":5,"status":"ok","ziel":5,"treffer":[5],"meldung":"Ader ist korrekt verbunden"}
```

## Projektstruktur

```text
Sub-D-Tester/
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── sub_d_tester/
│   ├── __init__.py
│   ├── config.py
│   ├── protocol.py
│   ├── serial_connection.py
│   ├── simulator.py
│   └── ui.py
├── arduino/
│   └── sub_d_tester_mega/
│       └── sub_d_tester_mega.ino
├── assets/
│   └── logo.svg
├── docs/
│   └── anschlussplan.md
├── tests/
│   └── test_protocol.py
└── .github/
    └── workflows/
        └── python-check.yml
```

## Tests

```bash
python -m unittest discover -s tests
```

Zusätzlich kann man die Python-Dateien kompilieren lassen:

```bash
python -m compileall .
```

## Fehlerbehebung

### Keine Verbindung zum Arduino

- Prüfen, ob der richtige COM-Port gewählt ist
- Arduino IDE Serial Monitor schließen
- USB-Kabel prüfen
- Baudrate auf `9600` lassen
- Unter Linux eventuell Rechte setzen:

```bash
sudo usermod -a -G dialout $USER
```

Danach neu anmelden oder neu starten.

### Alle Adern sind unterbrochen

- Prüfling richtig einstecken
- D-Sub-Adapter auf Eingang/Ausgang prüfen
- Pinbelegung im Sketch mit der echten Verdrahtung vergleichen
- Keine Spannung von außen einspeisen

### Viele Kurzschlüsse

- Lötstellen und Crimpkontakte prüfen
- Zinnbrücken am D-Sub-Stecker suchen
- Flachbandkabel auf falsche Orientierung prüfen
- Testadapter einzeln durchmessen

## Sicherheit

Der Tester ist nur für Kleinspannung, Logiksignale und spannungsfreie Leitungen gedacht. Keine Netzspannung, keine unbekannten Industrieanlagen und keine aktiven Signalleitungen direkt anschließen.

## Lizenz

MIT License. Copyright © 2026 Amir Mobahseraghdam.
