const byte ADER_ANZAHL = 25;
const unsigned long BAUDRATE = 9600;
const unsigned int SCHALTZEIT_MS = 12;
const unsigned int PAUSE_MS = 25;

const byte ausgangspins[ADER_ANZAHL] = {
  22, 23, 24, 25, 26,
  27, 28, 29, 30, 31,
  37, 38, 39, 40, 41,
  42, 43, 44, 45, 46
};

const byte eingangspins[ADER_ANZAHL] = {
  A0, A1, A2, A3, A4,
  A5, A6, A7, A8, A9,
  A10, A11, A12, A13, A14,
  A15, 2, 3, 4, 5,
  6, 7, 8, 9, 10
};

bool jsonFormat = true;

struct Ergebnis {
  byte pin;
  byte ziel;
  byte treffer[ADER_ANZAHL];
  byte anzahl;
  String status;
  String meldung;
};

void setup() {
  Serial.begin(BAUDRATE);
  Serial.setTimeout(100);
  vorbereiten();
  sendeBereit();
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String befehl = Serial.readStringUntil('\n');
  befehl.trim();
  befehl.toUpperCase();

  if (befehl.length() == 0) {
    sendeFehler("Leerer Befehl");
    return;
  }

  if (befehl == "TEST") {
    gesamttest();
    return;
  }

  if (befehl.startsWith("PIN ")) {
    verarbeitePinBefehl(befehl);
    return;
  }

  if (befehl == "STATUS") {
    sendeStatus();
    return;
  }

  if (befehl == "FORMAT JSON") {
    jsonFormat = true;
    sendeFormat("json");
    return;
  }

  if (befehl == "FORMAT TEXT") {
    jsonFormat = false;
    sendeFormat("text");
    return;
  }

  if (befehl == "RESET") {
    vorbereiten();
    sendeInfo("Pins wurden zurueckgesetzt");
    return;
  }

  if (befehl == "HILFE" || befehl == "HELP") {
    hilfe();
    return;
  }

  sendeFehler("Unbekannter Befehl");
}

void verarbeitePinBefehl(String befehl) {
  String wert = befehl.substring(4);
  wert.trim();

  if (!istZahl(wert)) {
    sendeFehler("Adernummer ist keine Zahl");
    return;
  }

  int nummer = wert.toInt();

  if (nummer < 1 || nummer > ADER_ANZAHL) {
    sendeFehler("Ungueltige Adernummer");
    return;
  }

  Ergebnis ergebnis = testeAder(nummer - 1);
  sendeErgebnis(ergebnis);
}

bool istZahl(String text) {
  if (text.length() == 0) {
    return false;
  }

  for (unsigned int i = 0; i < text.length(); i++) {
    if (!isDigit(text.charAt(i))) {
      return false;
    }
  }

  return true;
}

void vorbereiten() {
  for (byte i = 0; i < ADER_ANZAHL; i++) {
    pinMode(ausgangspins[i], INPUT);
    digitalWrite(ausgangspins[i], LOW);
    pinMode(eingangspins[i], INPUT_PULLUP);
  }
}

void gesamttest() {
  byte ok = 0;
  byte vertauscht = 0;
  byte kurzschluss = 0;
  byte unterbrochen = 0;

  sendeStart();

  for (byte i = 0; i < ADER_ANZAHL; i++) {
    Ergebnis ergebnis = testeAder(i);
    sendeErgebnis(ergebnis);

    if (ergebnis.status == "ok") {
      ok++;
    } else if (ergebnis.status == "vertauscht") {
      vertauscht++;
    } else if (ergebnis.status == "kurzschluss") {
      kurzschluss++;
    } else if (ergebnis.status == "unterbrochen") {
      unterbrochen++;
    }

    delay(PAUSE_MS);
  }

  vorbereiten();
  sendeEnde(ok, vertauscht, kurzschluss, unterbrochen);
}

Ergebnis testeAder(byte aderIndex) {
  Ergebnis ergebnis;
  ergebnis.pin = aderIndex + 1;
  ergebnis.ziel = 0;
  ergebnis.anzahl = 0;

  vorbereiten();

  pinMode(ausgangspins[aderIndex], OUTPUT);
  digitalWrite(ausgangspins[aderIndex], LOW);

  delay(SCHALTZEIT_MS);

  for (byte i = 0; i < ADER_ANZAHL; i++) {
    if (digitalRead(eingangspins[i]) == LOW) {
      ergebnis.treffer[ergebnis.anzahl] = i + 1;
      ergebnis.anzahl++;
    }
  }

  if (ergebnis.anzahl == 0) {
    ergebnis.status = "unterbrochen";
    ergebnis.meldung = "Keine Verbindung erkannt";
  } else if (ergebnis.anzahl == 1 && ergebnis.treffer[0] == aderIndex + 1) {
    ergebnis.status = "ok";
    ergebnis.ziel = ergebnis.treffer[0];
    ergebnis.meldung = "Ader ist korrekt verbunden";
  } else if (ergebnis.anzahl == 1) {
    ergebnis.status = "vertauscht";
    ergebnis.ziel = ergebnis.treffer[0];
    ergebnis.meldung = "Ader liegt auf einem anderen Kontakt";
  } else {
    ergebnis.status = "kurzschluss";
    ergebnis.meldung = "Mehrere Kontakte reagieren gleichzeitig";
  }

  vorbereiten();
  return ergebnis;
}

void sendeBereit() {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"bereit\",\"adern\":");
    Serial.print(ADER_ANZAHL);
    Serial.println("}");
  } else {
    Serial.print("BEREIT: ");
    Serial.print(ADER_ANZAHL);
    Serial.println(" Adern");
  }
}

void sendeStart() {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"start\",\"adern\":");
    Serial.print(ADER_ANZAHL);
    Serial.println("}");
  } else {
    Serial.print("TEST START: ");
    Serial.print(ADER_ANZAHL);
    Serial.println(" Adern");
  }
}

void sendeEnde(byte ok, byte vertauscht, byte kurzschluss, byte unterbrochen) {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"ende\",\"ok\":");
    Serial.print(ok);
    Serial.print(",\"vertauscht\":");
    Serial.print(vertauscht);
    Serial.print(",\"kurzschluss\":");
    Serial.print(kurzschluss);
    Serial.print(",\"unterbrochen\":");
    Serial.print(unterbrochen);
    Serial.println("}");
  } else {
    Serial.print("TEST ENDE: OK=");
    Serial.print(ok);
    Serial.print(", VERTAUSCHT=");
    Serial.print(vertauscht);
    Serial.print(", KURZSCHLUSS=");
    Serial.print(kurzschluss);
    Serial.print(", UNTERBROCHEN=");
    Serial.println(unterbrochen);
  }
}

void sendeErgebnis(Ergebnis ergebnis) {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"pin\",\"pin\":");
    Serial.print(ergebnis.pin);
    Serial.print(",\"status\":\"");
    Serial.print(ergebnis.status);
    Serial.print("\",\"ziel\":");
    Serial.print(ergebnis.ziel);
    Serial.print(",\"treffer\":[");

    for (byte i = 0; i < ergebnis.anzahl; i++) {
      if (i > 0) {
        Serial.print(",");
      }
      Serial.print(ergebnis.treffer[i]);
    }

    Serial.print("],\"meldung\":\"");
    Serial.print(ergebnis.meldung);
    Serial.println("\"}");
  } else {
    Serial.print("PIN ");
    Serial.print(ergebnis.pin);
    Serial.print(": ");
    Serial.print(ergebnis.status);
    Serial.print(", ZIEL ");
    Serial.print(ergebnis.ziel);
    Serial.print(", TREFFER [");

    for (byte i = 0; i < ergebnis.anzahl; i++) {
      if (i > 0) {
        Serial.print(",");
      }
      Serial.print(ergebnis.treffer[i]);
    }

    Serial.print("], ");
    Serial.println(ergebnis.meldung);
  }
}

void sendeStatus() {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"status\",\"bereit\":true,\"adern\":");
    Serial.print(ADER_ANZAHL);
    Serial.print(",\"format\":\"");
    Serial.print(jsonFormat ? "json" : "text");
    Serial.println("\"}");
  } else {
    Serial.print("STATUS: bereit, ");
    Serial.print(ADER_ANZAHL);
    Serial.print(" Adern, Format ");
    Serial.println(jsonFormat ? "json" : "text");
  }
}

void sendeFormat(const char* wert) {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"format\",\"wert\":\"");
    Serial.print(wert);
    Serial.println("\"}");
  } else {
    Serial.print("FORMAT: ");
    Serial.println(wert);
  }
}

void sendeInfo(const char* meldung) {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"info\",\"meldung\":\"");
    Serial.print(meldung);
    Serial.println("\"}");
  } else {
    Serial.print("INFO: ");
    Serial.println(meldung);
  }
}

void sendeFehler(const char* meldung) {
  if (jsonFormat) {
    Serial.print("{\"typ\":\"fehler\",\"meldung\":\"");
    Serial.print(meldung);
    Serial.println("\"}");
  } else {
    Serial.print("FEHLER: ");
    Serial.println(meldung);
  }
}

void hilfe() {
  if (jsonFormat) {
    Serial.println("{\"typ\":\"hilfe\",\"befehle\":[\"TEST\",\"PIN 1..25\",\"STATUS\",\"FORMAT JSON\",\"FORMAT TEXT\",\"RESET\",\"HILFE\"]}");
  } else {
    Serial.println("Befehle: TEST, PIN 1..25, STATUS, FORMAT JSON, FORMAT TEXT, RESET, HILFE");
  }
}
