# Kabeltest

Ein sauber aufgebautes Arduino- und Python-Projekt zum Prüfen von D-Sub-25 Kabeln, Leitungen und selbstgebauten Kabelbäumen. Die Software prüft bis zu 25 Adern auf Durchgang, Unterbrechung, Vertauschung und Kurzschluss. Dazu gehören eine moderne Desktop-Oberfläche in Python und ein Arduino-Sketch für den eigentlichen Leitungstest.

Das Projekt ist bewusst praktisch gehalten: Es soll im Labor, in der Werkstatt oder im Studium schnell verständlich sein, ohne dass man sich erst durch unnötig komplizierte Strukturen kämpfen muss.

## Kurzüberblick

- Prüfung von bis zu 25 Leitungen
- Arduino Mega als Mess- und Steuereinheit
- Python-Oberfläche mit CustomTkinter
- Anzeige jeder einzelnen Ader als eigene Prüfkarte
- Erkennung von korrekter Verbindung, Unterbrechung, Vertauschung und Kurzschluss
- Serielles JSON-Protokoll zwischen Arduino und Python
- Simulationsmodus ohne angeschlossene Hardware
- Vollbildmodus für Touchscreen- oder Werkstattbetrieb
- GitHub-fertige Projektstruktur

## Projektidee

Viele Kabeltests werden noch mit Multimeter, Papierliste und viel Geduld durchgeführt. Bei wenigen Leitungen ist das machbar. Bei 25-poligen Steckverbindern wird es schnell unübersichtlich. Dieses Projekt automatisiert genau diesen Ablauf.

Der Arduino legt nacheinander jede Ausgangsader auf LOW und liest auf der Gegenseite alle Eingänge aus. Dadurch erkennt das System, ob die erwartete Ader korrekt verbunden ist oder ob ein Fehler vorliegt. Die Python-Oberfläche zeigt das Ergebnis direkt sichtbar an.

## Geeignete Anwendungen

- D-Sub-25 Kabelprüfung
- Prüfung von Kabelbäumen
- Laboraufbau für Messtechnik
- Werkstattprüfung vor Inbetriebnahme
- Ausbildungsprojekt für Arduino und Python
- Demonstrator für HMI, Automatisierung und serielle Kommunikation

## Hardware

### Empfohlene Bauteile

| Bauteil | Zweck |
|---|---|
| Arduino Mega | Genügend I/O-Pins für 25 Leitungen |
| Zwei D-Sub-25 Buchsen | Kabelanschluss für Ein- und Ausgang |
| Terminal Block Shield | Saubere Verdrahtung ohne lose Steckbrücken |
| USB-Kabel | Verbindung zwischen PC und Arduino |
| Optionales Gehäuse | Mechanischer Schutz und bessere Bedienung |
| Optionales Touchdisplay | Lokaler Betrieb ohne PC möglich |

### Warum Arduino Mega?

Für 25 Leitungen werden viele Ein- und Ausgänge benötigt. Ein Arduino Uno reicht dafür nur mit zusätzlicher Hardware. Der Mega bietet genug Pins, ist gut verfügbar und bleibt für Lern- und Werkstattprojekte einfach verständlich.

## Pinbelegung

Die Standardbelegung im Arduino-Sketch ist so gewählt, dass sie auf einem Arduino Mega gut funktioniert.

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

Die Zuordnung kann im Sketch in den Arrays `ausgangspins` und `eingangspins` angepasst werden.

## Prüfprinzip

Für jede Ader läuft derselbe Ablauf:

1. Alle Ausgangspins werden hochohmig geschaltet.
2. Alle Eingangspins werden mit internem Pull-up vorbereitet.
3. Eine einzelne Ausgangsader wird auf LOW gesetzt.
4. Der Arduino liest alle Eingänge aus.
5. Aus den Treffern wird der Zustand berechnet.

### Ergebnisarten

| Status | Bedeutung |
|---|---|
| `ok` | Die Ader ist korrekt verbunden |
| `unterbrochen` | Es wurde keine Verbindung gefunden |
| `vertauscht` | Die Ader ist mit einem anderen Kontakt verbunden |
| `kurzschluss` | Mehrere Kontakte reagieren gleichzeitig |
| `fehler` | Die Antwort konnte nicht sauber verarbeitet werden |

## Serielle Befehle

Die Kommunikation läuft über USB-Serial mit 9600 Baud.

| Befehl | Wirkung |
|---|---|
| `TEST` | Startet den Gesamttest aller 25 Adern |
| `PIN 7` | Prüft nur Ader 7 |
| `STATUS` | Gibt den aktuellen Grundstatus zurück |
| `FORMAT JSON` | Aktiviert JSON-Ausgabe |
| `HILFE` | Gibt die verfügbaren Befehle aus |

Beispielantwort:

```json
{"typ":"pin","pin":5,"status":"ok","ziel":5,"treffer":[5],"meldung":"Ader ist korrekt verbunden"}
```

## Software

Die Desktop-Anwendung ist in Python geschrieben und verwendet CustomTkinter. Sie kann direkt mit dem Arduino arbeiten oder im Simulationsmodus ohne Hardware gestartet werden.

### Funktionen der Oberfläche

- Verbindung zu einem frei wählbaren COM-Port
- Start eines Gesamttests
- Einzeltest einer bestimmten Ader
- Live-Anzeige pro Ader
- Fortschrittsanzeige
- Ergebnisstatistik
- Prüfprotokoll mit Zeitstempel
- Simulationsmodus für Vorführung und Entwicklung
- Vollbildmodus für Touchscreen-Bedienung

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/DEIN-BENUTZERNAME/Kabeltest.git
cd Kabeltest
```

### 2. Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. Arduino-Sketch hochladen

Die Datei befindet sich hier:

```text
arduino/kabeltest_mega/kabeltest_mega.ino
```

In der Arduino IDE:

1. Board auf Arduino Mega stellen
2. Richtigen Port auswählen
3. Sketch öffnen
4. Hochladen

### 4. Python-Oberfläche starten

```bash
python main.py
```

Fenstermodus:

```bash
python main.py --fenster
```

Mit bestimmtem Port:

```bash
python main.py --port COM7
```

Mit Simulation:

```bash
python main.py --simulation --fenster
```

Unter Linux kann der Port zum Beispiel so aussehen:

```bash
python main.py --port /dev/ttyACM0 --fenster
```

Unter macOS zum Beispiel:

```bash
python main.py --port /dev/cu.usbmodem14101 --fenster
```

## requirements.txt

```text
customtkinter
pyserial
```

## Projektstruktur

```text
Kabeltest/
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── arduino/
│   └── kabeltest_mega/
│       └── kabeltest_mega.ino
├── assets/
│   └── logo.svg
├── docs/
│   └── screenshots/
│       └── .gitkeep
└── .github/
    └── workflows/
        └── python-check.yml
```

## Bedienung

1. Arduino per USB verbinden.
2. Port in der Oberfläche eintragen.
3. Auf `Verbinden` klicken.
4. Kabel zwischen die beiden D-Sub-25 Anschlüsse stecken.
5. `Gesamttest starten` drücken.
6. Ergebnis in der Oberfläche prüfen.

Für einzelne Leitungen kann eine Adernummer ausgewählt und mit `Einzeltest` geprüft werden.

## Test ohne Hardware

Der Simulationsmodus ist praktisch, um die Oberfläche zu zeigen oder weiterzuentwickeln, ohne den Arduino anzuschließen.

```bash
python main.py --simulation --fenster
```

Dabei erzeugt die Anwendung realistische Beispielergebnisse für alle 25 Adern.

## Fehlerbehebung

### Arduino wird nicht verbunden

- Prüfen, ob das USB-Kabel korrekt steckt
- Richtigen COM-Port auswählen
- Arduino IDE Serial Monitor schließen
- Baudrate auf 9600 setzen
- Treiber für das Board prüfen
- Unter Linux Benutzer zur Gruppe `dialout` hinzufügen

```bash
sudo usermod -a -G dialout $USER
```

Danach einmal abmelden oder neu starten.

### Python meldet fehlende Module

```bash
pip install -r requirements.txt
```

### Keine Treffer bei allen Adern

- D-Sub-Verdrahtung prüfen
- Gemeinsame Masse prüfen
- Eingang und Ausgang nicht vertauschen
- Pinbelegung im Sketch mit der realen Verdrahtung vergleichen

### Viele Kurzschlüsse

- Lötstellen prüfen
- Stecker auf Zinnbrücken kontrollieren
- Flachbandkabel auf falsche Crimpung prüfen
- Testadapter einzeln durchmessen

## Hinweise zur Sicherheit

Dieses Projekt ist für Kleinspannung und Logiksignale gedacht. Es darf nicht direkt an Netzspannung oder unbekannte Industrieanlagen angeschlossen werden. Vor jedem Test sollte sichergestellt werden, dass das Kabel spannungsfrei ist.

## Mögliche Erweiterungen

- Speicherung der Testergebnisse als CSV
- PDF-Prüfprotokoll
- Touchdisplay-Bedienung direkt am Arduino
- Automatische Seriennummerneingabe
- Barcode- oder QR-Code-Scanner
- SQLite-Datenbank für Kabeltypen
- Benutzerverwaltung
- Mehrsprachige Oberfläche
- Prüfprofile für verschiedene Steckertypen
- Kalibrierfunktion für Testadapter

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details stehen in der Datei `LICENSE`.

## Autor

Joe2824

## Kurzbeschreibung für GitHub

Arduino- und Python-basierter Kabeltester für bis zu 25 Leitungen mit grafischer Oberfläche, JSON-Serial-Protokoll und D-Sub-25 Prüfaufbau.
