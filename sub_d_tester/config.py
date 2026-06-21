from __future__ import annotations

APP_NAME = "Sub-D-Tester"
AUTHOR = "Amir Mobahseraghdam"
VERSION = "2.0.0"
WIRE_COUNT = 25
DEFAULT_BAUDRATE = 9600
DEFAULT_PORT_WINDOWS = "COM9"
DEFAULT_PORT_UNIX = "/dev/ttyACM0"

STATUS_LABELS = {
    "nicht_geprueft": "Nicht geprüft",
    "aktiv": "Wird geprüft",
    "ok": "In Ordnung",
    "unterbrochen": "Unterbrochen",
    "vertauscht": "Vertauscht",
    "kurzschluss": "Kurzschluss",
    "fehler": "Fehler",
}

STATUS_COLORS = {
    "nicht_geprueft": ("#E5E7EB", "#475569"),
    "aktiv": ("#DBEAFE", "#1D4ED8"),
    "ok": ("#DCFCE7", "#166534"),
    "unterbrochen": ("#FEE2E2", "#991B1B"),
    "vertauscht": ("#FEF3C7", "#92400E"),
    "kurzschluss": ("#FFE4E6", "#9F1239"),
    "fehler": ("#F3E8FF", "#6B21A8"),
}

STATUS_ORDER = ("ok", "unterbrochen", "vertauscht", "kurzschluss", "fehler")
