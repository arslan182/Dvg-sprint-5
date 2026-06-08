# Dvg-Sprint-5 – RPA-Bot für die ERP-Rechnungserfassung

**Hochschule Karlsruhe** | Modul: Digitalisierung von Geschäftsprozessen | Gruppe G11

---

## Was ist Sprint-5?

Sprint 5 baut auf dem Camunda-Workflow aus Sprint 4 auf. Wir haben einen UiPath RPA-Bot gebaut, der den bisher manuellen Schritt "Rechnungsdaten im ERP-System eingeben" automatisiert. Der Bot öffnet das ERP-Frontend im Browser und füllt das Formular selbstständig mit den Rechnungsdaten aus — und als optionales Extra haben wir ihn direkt in den Camunda-Prozess eingebunden, sodass alles automatisch läuft.

Der Bot läuft als Unattended Bot in der UiPath Cloud und wird automatisch vom Python Worker über die UiPath StartJobs API gestartet.

---

## Architektur

```
Camunda 8 SaaS (BPMN-Prozess)
        │
        │  Zeebe Jobs
        ▼
  Python Worker (pyzeebe)
   ├── auto_workers.py   → automatische Service Tasks
   ├── grpc_worker.py    → Metadaten per gRPC speichern
   └── payment_worker.py → Zahlung per RabbitMQ senden
        │
        ├──▶ gRPC Server → PostgreSQL Datenbank
        └──▶ RabbitMQ Queue → Payment Consumer
```

---

## Projektstruktur

```
Dvg-sprint-5/
├── src/
│   ├── workers/
│   │   ├── auto_workers.py        # Automatische Camunda Job Worker
│   │   ├── grpc_worker.py         # Worker für Metadaten per gRPC
│   │   └── payment_worker.py      # Worker für Zahlung per RabbitMQ
│   ├── invoice_metadata/
│   │   ├── server.py              # gRPC Server (aus Sprint 2)
│   │   ├── invoice.proto          # Protobuf Definition
│   │   ├── invoice_pb2.py
│   │   └── invoice_pb2_grpc.py
│   ├── payment_system/
│   │   └── payment.py             # RabbitMQ Consumer (aus Sprint 2)
│   └── camunda/
│       ├── Workflow-Sprint-4.bpmn # BPMN-Prozess (angepasst für Sprint 5)
│       └── compliance_check.dmn   # DMN Entscheidungstabelle
├── tests/
│   └── test_workers.py
├── extras/
│   └── compose/
│       ├── RabbitMQ/docker-compose.yml
│       └── postgres/docker-compose.yml
├── docs/
│   ├── documentation.md           # Sprint 4 Dokumentation
│   └── sprint5_dokumentation.md   # Sprint 5 Dokumentation (RPA)
├── logs/
│   └── README.md
├── erp_frontend.html              # ERP-Frontend (GitHub Pages deployed)
├── rechnung_data.json             # Testdaten für den RPA-Bot
├── start_process.py
├── send_correction.py
├── .env
├── requirements.txt
└── README.md
```

---

## Voraussetzungen

- Python 3.10+
- Docker
- Camunda 8 SaaS Account

```bash
pip install -r requirements.txt
```

---

## Einrichtung

### 1. Umgebungsvariablen

`.env` Datei im Projektroot anlegen:

```
CAMUNDA_CLIENT_ID=...
CAMUNDA_CLIENT_SECRET=...
CAMUNDA_CLUSTER_ID=...
CAMUNDA_REGION=bru-2

GRPC_HOST=localhost
GRPC_PORT=50051

RABBITMQ_HOST=localhost
RABBITMQ_USER=user
RABBITMQ_PASSWORD=password

DB_HOST=localhost
DB_NAME=invoice_db
DB_USER=admin
DB_PASSWORD=...

UIPATH_CLIENT_ID=...
UIPATH_CLIENT_SECRET=...
UIPATH_ORG=gruppe11dvg
UIPATH_TENANT=DefaultTenant
UIPATH_FOLDER_ID=7919369
UIPATH_QUEUE_NAME=ERP-Rechnungen
UIPATH_PROCESS_NAME=RPA Workflow
UIPATH_POLL_INTERVAL=5
UIPATH_POLL_RETRIES=30
UIPATH_JOB_TIMEOUT_MS=180000
```

### 2. Docker starten

```bash
cd extras/compose/postgres && docker-compose up -d
cd extras/compose/RabbitMQ && docker-compose up -d
```

---

## Starten

**Terminal 1** – Docker (PostgreSQL + RabbitMQ):
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

**Prozess starten:**
```bash
python start_process.py
```

---

## Prozessablauf

Der Prozess heißt **Workflow-Sprint-4** in Camunda 8 SaaS.

### Automatische Tasks

| Task | Worker | Beschreibung |
|------|--------|--------------|
| rechnung-erfassen | auto_workers.py | Zeitstempel und Status setzen |
| automatische-validierung | auto_workers.py | Pflichtfelder prüfen |
| compliance-check | auto_workers.py | Schwellenwert prüfen |
| uipath-erp-queue | auto_workers.py | UiPath Bot starten (StartJobs API) |
| save-invoice-metadata | grpc_worker.py | Metadaten per gRPC speichern |
| initiate-payment | payment_worker.py | Zahlungsauftrag per RabbitMQ |
| rechnung-archivieren | auto_workers.py | Archivieren |

### Manuelle Tasks (User Tasks in Camunda Tasklist)

- Metadaten aus Rechnung manuell extrahieren
- Rechnung Validieren
- Compliance-Fall manuell prüfen
- Rechnung freigeben

### Fehlerbehandlung (Boundary Error Events)

**gRPC nicht erreichbar** → Metadaten manuell speichern  
**RabbitMQ nicht erreichbar** → Zahlung manuell erfassen

### Prozesswege

**Normalfall (Email):**
Rechnung eingang → Metadaten manuell extrahieren → Rechnung validieren → Compliance Check → Rechnung freigeben → gRPC speichern → ERP eingeben → RabbitMQ Zahlung → Archivieren

**Compliance-Verstoß:**
Betrag über Schwellenwert → Compliance manuell prüfen → Freigeben oder Zurückweisen

---

## Compliance-Schwellenwerte

| Währung | Schwellenwert |
|---------|--------------|
| EUR     | > 10.000     |
| USD     | > 11.000     |
| CHF     | > 10.800     |
| GBP     | > 8.700      |

---

## Tests

```bash
$env:PYTHONPATH = "."; pytest tests/test_workers.py -v
```

---

## Korrektur senden

Wenn ein Prozess auf fehlende Informationen wartet:

```bash
python send_correction.py R-001
```

---

## RPA-Bot (Sprint 5)

Der Bot läuft als Unattended Cloud Robot in UiPath Orchestrator (Folder: Solution). Er wird automatisch vom Python Worker über die UiPath StartJobs API gestartet, sobald Camunda den Task `uipath-erp-queue` picked.

Der Bot öffnet das ERP-Frontend in Edge und füllt das Formular per JavaScript Injection aus. Die Rechnungsdaten (Nummer, Lieferant, Betrag, Währung, Eingangskanal) werden als InputArguments vom Camunda Worker übergeben.

Das ERP-Frontend ist erreichbar unter:
```
https://arslan182.github.io/Dvg-sprint-5/erp_frontend.html
```

### UiPath Konfiguration

- **Org:** gruppe11dvg
- **Tenant:** DefaultTenant
- **Folder:** Solution (ID: 7919369)
- **Process:** RPA Workflow (v1.0.2)
- **Robot:** Default Robot (Unattended, Cloud Serverless)
- **External App:** Camunda-Connector (OAuth2 Client Credentials)
- **App Scopes:** OR.Jobs, OR.Jobs.Write, OR.Execution, OR.Execution.Write, OR.Queues, OR.Queues.Read, OR.Queues.Write

---

## Bekannte Einschränkungen

- Der Camunda Trial Cluster pausiert automatisch nach längerer Inaktivität — vor dem Testen prüfen ob er noch läuft.
- Prozessvariablen die vom Worker gesetzt werden (z.B. `validierung_erfolgreich`, `compliance_notwendig`) sollten beim Start nicht manuell mitgegeben werden.
- Für `rechnung_freigegeben` wird eine Checkbox verwendet statt Dropdown, da Dropdowns nur Strings speichern.
- Der UiPath Bot läuft in einer Cloud-Session — das ausgefüllte Formular ist nur im UiPath Live Stream sichtbar, nicht im lokalen Browser.
