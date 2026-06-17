const byte ADER_ANZAHL = 25;

const byte ausgangspins[ADER_ANZAHL] = {
  22, 23, 24, 25, 26,
  27, 28, 29, 30, 31,
  32, 33, 34, 35, 36,
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

void setup() {
  Serial.begin(9600);
  vorbereiten();
  Serial.println("{\"typ\":\"bereit\",\"adern\":25}");
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String befehl = Serial.readStringUntil('\n');
  befehl.trim();
  befehl.toUpperCase();

  if (befehl == "TEST") {
    gesamttest();
    return;
  }

  if (befehl.startsWith("PIN ")) {
    int nummer = befehl.substring(4).toInt();
    if (nummer >= 1 && nummer <= ADER_ANZAHL) {
      testeAder(nummer - 1);
    } else {
      Serial.println("{\"typ\":\"fehler\",\"meldung\":\"Ungueltige Adernummer\"}");
    }
    return;
  }

  if (befehl == "STATUS") {
    Serial.println("{\"typ\":\"status\",\"bereit\":true,\"adern\":25}");
    return;
  }

  if (befehl == "FORMAT JSON") {
    jsonFormat = true;
    Serial.println("{\"typ\":\"format\",\"wert\":\"json\"}");
    return;
  }

  if (befehl == "HILFE") {
    hilfe();
    return;
  }

  Serial.println("{\"typ\":\"fehler\",\"meldung\":\"Unbekannter Befehl\"}");
}

void vorbereiten() {
  for (byte i = 0; i < ADER_ANZAHL; i++) {
    pinMode(ausgangspins[i], INPUT);
    pinMode(eingangspins[i], INPUT_PULLUP);
  }
}

void gesamttest() {
  Serial.println("{\"typ\":\"start\",\"adern\":25}");
  for (byte i = 0; i < ADER_ANZAHL; i++) {
    testeAder(i);
    delay(25);
  }
  vorbereiten();
  Serial.println("{\"typ\":\"ende\"}");
}

void testeAder(byte aderIndex) {
  byte treffer[ADER_ANZAHL];
  byte anzahl = 0;

  vorbereiten();
  pinMode(ausgangspins[aderIndex], OUTPUT);
  digitalWrite(ausgangspins[aderIndex], LOW);
  delay(12);

  for (byte i = 0; i < ADER_ANZAHL; i++) {
    if (digitalRead(eingangspins[i]) == LOW) {
      treffer[anzahl] = i + 1;
      anzahl++;
    }
  }

  if (anzahl == 0) {
    sendeErgebnis(aderIndex + 1, "unterbrochen", 0, treffer, anzahl, "Keine Verbindung erkannt");
  } else if (anzahl == 1 && treffer[0] == aderIndex + 1) {
    sendeErgebnis(aderIndex + 1, "ok", treffer[0], treffer, anzahl, "Ader ist korrekt verbunden");
  } else if (anzahl == 1) {
    sendeErgebnis(aderIndex + 1, "vertauscht", treffer[0], treffer, anzahl, "Ader liegt auf einem anderen Kontakt");
  } else {
    sendeErgebnis(aderIndex + 1, "kurzschluss", 0, treffer, anzahl, "Mehrere Kontakte reagieren gleichzeitig");
  }

  vorbereiten();
}
yte treffer[], byte anzahl, const char* meldung) {
  Serial.print("{\"typ\":\"pin\",\"pin\":");
  Serial.print(pin);
  Serial.print(",\"status\":\"");
  Serial.print(status);
  Serial.print("\",\"ziel\":");
  Serial.print(ziel);
  Serial.print(",\"treffer\":[");
  for (byte i = 0; i < anzahl; i++) {
    if (i > 0) {
      Serial.print(",");
    }
    Serial.print(treffer[i]);
  }
  Serial.print("],\"meldung\":\"");
  Serial.print(meldung);
  Serial.println("\"}");
}

void hilfe() {
  Serial.println("Befehle: TEST, PIN 1..25, STATUS, FORMAT JSON, HILFE");
}
