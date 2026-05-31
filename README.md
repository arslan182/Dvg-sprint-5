# Sprint 4 – Digitalisierung von Geschäftsprozessen

**Hochschule Karlsruhe** | Modul: Digitalisierung von Geschäftsprozessen  
**Gruppe:** G11

---

## Worum geht es?

In Sprint 4 haben wir den Rechnungsverarbeitungsprozess als BPMN-Workflow in **Camunda 8 SaaS** modelliert und mit echten Job Workern verbunden. Die Worker kommunizieren dabei mit den Diensten aus Sprint 2 – also dem gRPC-Server für Metadaten und RabbitMQ für Zahlungsaufträge.

Der Prozess bildet den kompletten Weg einer Rechnung ab: vom Eingang über Validierung, Compliance-Prüfung, Freigabe, bis hin zur Archivierung. Dabei gibt es sowohl automatische als auch manuelle Pfade, je nachdem ob die Dienste erreichbar sind oder nicht.

---

## Projektstruktur

```
src/
├── workers/
│   ├── auto_workers.py       # Automatische Camunda Job Worker
│   ├── grpc_worker.py        # Worker für gRPC Metadaten-Speicherung
│   └── payment_worker.py     # Worker für RabbitMQ Zahlungsauftrag
├── camunda/
│   └── Workflow-Sprint-4.bpmn  # BPMN Prozessmodell
├── invoice_metadata/         # Aus Sprint 2 – gRPC Server
└── payment_system/           # Aus Sprint 2 – RabbitMQ Consumer
```

---

## Dateien erklärt

### `auto_workers.py`
Hier sind alle automatischen Service Tasks als Camunda Job Worker zusammengefasst. Der Worker läuft dauerhaft und wartet auf Jobs von Camunda:

- **rechnung-erfassen** – Setzt Zeitstempel und Status wenn eine neue Rechnung eingeht
- **automatische-validierung** – Prüft ob alle Pflichtfelder vorhanden sind (Rechnungsnummer, Lieferant, Betrag, Währung, Datum). Gibt `validierung_erfolgreich = true/false` zurück.
- **compliance-check** – Prüft ob der Betrag über 10.000 EUR liegt. Wenn ja, muss eine manuelle Compliance-Prüfung stattfinden (`compliance_notwendig = true`).
- **send-request-email** – Simuliert das Versenden einer E-Mail an den Lieferanten wenn Informationen fehlen.
- **rechnung-archivieren** – Archiviert die Rechnung am Ende des Prozesses.

### `grpc_worker.py`
Verbindet Camunda mit dem gRPC-Server aus Sprint 2. Wenn der Task `save-invoice-metadata` in Camunda ausgelöst wird, sendet dieser Worker die Rechnungsdaten per gRPC an den Server, der sie dann in der PostgreSQL-Datenbank speichert.

Wenn der gRPC-Server nicht erreichbar ist, wirft der Worker einen `BusinessError` – Camunda fängt das über den Boundary Error Event ab und leitet den Prozess zum manuellen Fallback "Metadaten manuell speichern".

### `payment_worker.py`
Verbindet Camunda mit RabbitMQ aus Sprint 2. Wenn der Task `initiate-payment` ausgelöst wird, schickt dieser Worker einen Zahlungsauftrag in die Queue `zahlungs_auftraege`.

Gleich wie beim gRPC Worker: wenn RabbitMQ nicht erreichbar ist, kommt ein `BusinessError` und der Prozess geht zu "Zahlung manuell erfassen".

---

## Prozessablauf

Der BPMN-Prozess hat folgende Hauptpfade:

**Normaler Weg (EDI):**
Rechnung erfassen → Automatische Validierung → Compliance Check → Rechnung freigeben → gRPC speichern → ERP eingeben → RabbitMQ Zahlung → Archivieren

**Manueller Weg (Email/Portal):**
Rechnung erfassen → Metadaten manuell extrahieren → Rechnung validieren → weiter wie oben

**Fehlerbehandlung:**
- gRPC nicht erreichbar → Metadaten manuell speichern
- RabbitMQ nicht erreichbar → Zahlung manuell erfassen
- Validierung fehlgeschlagen → Fehlende Informationen anfordern → Reminder → Zurückweisen
- Compliance-Verstoß → Compliance manuell prüfen → Freigeben oder Zurückweisen

---

## Voraussetzungen

- Python 3.10+
- Camunda 8 SaaS Account (cloud.camunda.io)
- Docker (für RabbitMQ und PostgreSQL aus Sprint 2)
- Die Sprint-2 Services müssen laufen

Python-Pakete installieren:
```bash
pip install pyzeebe grpcio pika psycopg2-binary
```

---

## Starten

Je nachdem welchen Pfad man testen möchte, müssen unterschiedliche Dienste laufen.

### Automatischer Weg (gRPC + RabbitMQ funktionieren)

**Terminal 1** – Sprint 2 Backend starten:
```bash
docker-compose up
```

**Terminal 2** – gRPC Server:
```bash
python -m src.invoice_metadata.server
```

**Terminal 3** – Auto Workers:
```bash
python src/workers/auto_workers.py
```

**Terminal 4** – gRPC Worker:
```bash
python src/workers/grpc_worker.py
```

**Terminal 5** – Payment Worker:
```bash
python src/workers/payment_worker.py
```

### Manueller Fallback (gRPC/RabbitMQ nicht verfügbar)

Einfach `server.py` und/oder Docker nicht starten. Die Worker werfen dann automatisch einen `BusinessError` und der Prozess geht den manuellen Weg.

> **Hinweis für AppLocker-Umgebungen:** Falls Python blockiert wird, den Python-Pfad aus einem bestehenden venv verwenden, z.B.:  
> `C:\Users\...\fastapi-gruppe-3\.venv\Scripts\python.exe src/workers/auto_workers.py`

---

## Prozess starten

1. In Camunda Operate oder Tasklist einloggen
2. Neuen Prozess starten mit folgenden Variablen:

**EDI-Weg (automatisch):**
```json
{
  "eingangskanal": "edi",
  "rechnungs_nummer": "R-001",
  "lieferant": "Test GmbH",
  "betrag": 5000,
  "waehrung": "EUR",
  "datum": "2026-05-30",
  "rechnung_genehmigt": true,
  "informationen_erhalten": true
}
```

**Email-Weg (manuell extrahieren):**
```json
{
  "eingangskanal": "email",
  "rechnungs_nummer": "R-002",
  "lieferant": "Test GmbH",
  "betrag": 5000,
  "waehrung": "EUR",
  "datum": "2026-05-30",
  "rechnung_genehmigt": true,
  "informationen_erhalten": true
}
```

**Compliance-Prüfung notwendig (Betrag über 10.000):**
```json
{
  "eingangskanal": "edi",
  "rechnungs_nummer": "R-003",
  "lieferant": "Test GmbH",
  "betrag": 15000,
  "waehrung": "EUR",
  "datum": "2026-05-30",
  "rechnung_genehmigt": true,
  "informationen_erhalten": true
}
```

---

## Camunda Verbindung

Die Credentials für den Camunda SaaS Cluster werden als Umgebungsvariablen gesetzt oder sind direkt in den Worker-Dateien als Fallback hinterlegt:

| Variable | Beschreibung |
|---|---|
| `CAMUNDA_CLIENT_ID` | Client ID aus dem Camunda Console |
| `CAMUNDA_CLIENT_SECRET` | Client Secret |
| `CAMUNDA_CLUSTER_ID` | Cluster ID |
| `CAMUNDA_REGION` | Region (z.B. bru-2) |
| `GRPC_HOST` | Host des gRPC Servers (Standard: localhost) |
| `GRPC_PORT` | Port des gRPC Servers (Standard: 50051) |
| `RABBITMQ_HOST` | RabbitMQ Host (Standard: localhost) |

---

## Bekannte Besonderheiten

- Der Camunda Trial Cluster pausiert automatisch nach Inaktivität. Vor dem Testen auf cloud.camunda.io prüfen ob der Cluster läuft.
- Die Boundary Error Events funktionieren nur mit `BusinessError` aus pyzeebe – normale Python Exceptions lösen keinen Boundary Event aus, sondern erzeugen einen Incident.
- Das Formular-Dropdown für `rechnung_freigegeben` speichert Strings, nicht Booleans. Deswegen haben wir auf eine Checkbox umgestellt.
- Prozessvariablen die vom Worker gesetzt werden (z.B. `validierung_erfolgreich`, `compliance_notwendig`) sollten nicht manuell beim Start mitgegeben werden, da die Worker sie überschreiben.

---

## Verbindung zu Sprint 2

Dieser Sprint baut direkt auf Sprint 2 auf:

| Sprint 2 Dienst | Wird verwendet von |
|---|---|
| `invoice_metadata.server` (gRPC) | `grpc_worker.py` |
| `payment_system/payment.py` (RabbitMQ Consumer) | `payment_worker.py` |
| PostgreSQL Datenbank | Über gRPC Server |
| RabbitMQ Queue `zahlungs_auftraege` | `payment_worker.py` |
