# Anschlussplan

Dieses Dokument beschreibt die Standardverdrahtung für den Sub-D-Tester mit Arduino Mega.

## Prinzip

Jede Ader besitzt eine Ausgangsseite und eine Eingangsseite. Beim Test wird immer nur eine Ausgangsader aktiv auf LOW gezogen. Die Eingangsseite arbeitet mit internem Pull-up. Dadurch erkennt der Arduino, welcher Eingang ebenfalls LOW wird.

## Standardbelegung

| Ader | Ausgang Arduino Mega | Eingang Arduino Mega |
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

## Hinweise für den Aufbau

- Die Prüflinge müssen spannungsfrei sein.
- Ausgangs- und Eingangsseite sollten mechanisch eindeutig beschriftet sein.
- Für die Werkstatt ist eine Frontplatte mit zwei D-Sub-25 Anschlüssen sinnvoll.
- Vor dem ersten Test sollte der Adapter ohne Prüfling durchgemessen werden.
