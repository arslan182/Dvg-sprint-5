# Dokumentation – Sprint 5

**Modul:** Digitalisierung von Geschäftsprozessen  
**Hochschule:** Hochschule Karlsruhe  
**Gruppe:** G11

---

## Was war die Aufgabe?

In Sprint 5 sollten wir einen RPA-Bot mit UiPath bauen, der die Eingabe von Rechnungsdaten in unser ERP-Frontend automatisiert. Das klingt erstmal einfach, hat aber etwas länger gedauert als erwartet — dazu später mehr.

Die Aufgaben waren:

- **5.1** Bot implementieren, der das ERP-Formular automatisch ausfüllt
- **5.2** Den Bot testen und dokumentieren
- **5.3** (optional) Bot in den Camunda-Workflow einbinden

Wir haben alle drei Punkte umgesetzt.

---

## Tool: UiPath Studio Web

Wir haben UiPath Studio Web verwendet, das läuft komplett im Browser und der Bot wird in der UiPath Cloud ausgeführt. Kein lokaler Robot nötig.

Das ERP-Frontend hatten wir auf GitHub Pages deployed:
`https://arslan182.github.io/Dvg-sprint-5/erp_frontend.html`

---

## Implementierung (5.1)

### Erster Ansatz: TypeInto-Aktivitäten

Der Plan war, mit den Standard-UiPath-Aktivitäten `TypeInto` und `SelectItem` die Felder zu befüllen — so wie man es normalerweise macht. Wir haben die Felder mit dem "Indicate Target" Tool aufgenommen und die Variablen zugewiesen.

Das Problem: Der Bot ist beim Start jedes Mal bei "Healing agent configuration" hängengeblieben. Er hat den Browser geöffnet, aber dann nichts mehr gemacht. Wir haben versucht die Selektoren neu aufzunehmen, den Healing Agent deaktiviert und verschiedene Einstellungen probiert — aber der Bot ist immer wieder an der gleichen Stelle hängen geblieben.

### Lösung: JavaScript Injection

Nach einiger Fehlersuche haben wir uns für einen anderen Weg entschieden: statt die Felder per Mausklick und Tastatur zu befüllen, haben wir eine `Inject Js Script` Aktivität verwendet. Der Bot führt direkt JavaScript im Browser aus und setzt die Feldwerte über die HTML-IDs.

Das funktioniert deutlich stabiler, weil es nicht von Selektoren abhängt die sich je nach Browser-State ändern können. JavaScript Injection ist eine anerkannte RPA-Technik, gerade wenn die UI nicht gut für Automatisierung geeignet ist oder Selektor-Probleme auftauchen.

### Workflow-Struktur

```
Manual Trigger
└── Use Browser Edge: ERP-System – Rechnungserfassung
    │   URL: https://arslan182.github.io/Dvg-sprint-5/erp_frontend.html
    │
    └── Inject Js Script
        → Alle Felder per getElementById mit den Input Arguments befüllen
        → Formular abschicken
```

### Input Arguments

Der Workflow empfängt folgende Input Arguments, die beim Start vom Camunda Worker übergeben werden:

| Argument | Typ | Beschreibung |
|----------|-----|--------------|
| in_rechnungs_nummer | String | Rechnungsnummer aus dem Prozess |
| in_lieferant | String | Lieferantenname |
| in_betrag | String | Rechnungsbetrag |
| in_waehrung | String | Währung (EUR, USD, etc.) |
| in_eingangskanal | String | Eingangskanal (email, EDI, Portal) |

### JavaScript-Code

```javascript
function (element, input) {
  document.getElementById('rechnungs_nummer').value = input.rechnungs_nummer;
  document.getElementById('lieferant').value = input.lieferant;
  document.getElementById('betrag').value = input.betrag;
  document.getElementById('waehrung').value = input.waehrung;
  document.getElementById('eingangskanal').value = input.eingangskanal;
  document.getElementById('datum').valueAsDate = new Date();
  document.querySelector('button[type=submit]').click();
}
```

---

## Test (5.2)

### Testergebnis

Der Bot wurde erfolgreich ausgeführt. Alle Aktivitäten liefen ohne Fehler durch:

```
RPA Workflow execution started
Using Web App. Browser: Edge
URL: https://arslan182.github.io/Dvg-sprint-5/erp_frontend.html
Healing agent configuration.
RPA Workflow execution ended
```

Gesamtlaufzeit: ca. 27 Sekunden (Cloud Serverless). Alle Aktivitäten zeigten Status "Successful".

Da der Bot als Unattended Bot in der UiPath Cloud läuft, passiert die Ausführung in einer separaten Browser-Session — nicht im lokalen Browser. Das Ergebnis ist im UiPath Live Stream und in den Aktivitäts-Vorschaubildern von Studio Web sichtbar.

### Was wir beim Testen gelernt haben

- Der "Healing agent configuration" Log-Eintrag erscheint immer beim Start, auch wenn der Healing Agent deaktiviert ist — das ist nur eine Initialisierungsmeldung, kein Fehler
- Der Bot läuft in einer Cloud-Session, deshalb sieht man das ausgefüllte Formular nicht im eigenen Browser
- TypeInto-Aktivitäten hatten Selektor-Probleme mit der GitHub Pages URL — JavaScript Injection war zuverlässiger

---

## Einbindung in Camunda (5.3)

### Überblick

Den Bot haben wir vollständig in den Camunda-Prozess eingebunden. Der bisherige User Task "Rechnungsdaten im ERP-System eingeben" ist jetzt ein automatischer Service Task vom Typ `uipath-erp-queue`, der von unserem Python Worker (`auto_workers.py`) verarbeitet wird.

Der Worker holt sich einen OAuth2-Token von UiPath, ruft die StartJobs API auf und übergibt dabei die aktuellen Rechnungsdaten als InputArguments — die kommen direkt aus den Camunda-Prozessvariablen. Danach pollt der Worker alle 5 Sekunden den Job-Status bis der Bot fertig ist, bevor er den Camunda-Task abschließt.

### Ablauf

```
Camunda Task: uipath-erp-queue
        │
        ▼
auto_workers.py → OAuth2 Token holen
        │
        ▼
UiPath StartJobs API (POST)
        │    Header: X-UIPATH-OrganizationUnitId: 7919369
        │    Body: ReleaseName, Strategy, InputArguments (JSON)
        ▼
UiPath Orchestrator startet Bot auf Default Serverless Machine
        │
        ▼
Bot öffnet ERP-Frontend, füllt Formular mit echten Daten aus
```

### UiPath Konfiguration

Damit das funktioniert, mussten wir in UiPath einiges einrichten:

**External Application (OAuth2):**
- Name: Camunda-Connector
- Typ: Confidential (Client Credentials Flow)
- Scopes: OR.Jobs, OR.Jobs.Write, OR.Execution, OR.Execution.Write, OR.Queues, OR.Queues.Read, OR.Queues.Write

**Folder-Zugang:**
- Folder "Solution" → Manage Access → Camunda-Connector als "Automation User" + "Folder Administrator" hinzugefügt
- Folder "Solution" → Manage Access → Default Robot (Unattended) als "Automation User" hinzugefügt

**Robot:**
- Default Robot (Robot Account, Unattended) ist dem Folder Solution zugewiesen
- Machine: Default Serverless (Cloud Robot)

### Python Worker

Der Task `uipath-erp-queue` in `auto_workers.py` macht folgendes:

1. OAuth2-Token von `https://cloud.uipath.com/{org}/identity_/connect/token` holen
2. POST auf die StartJobs API mit den Rechnungsdaten als InputArguments
3. Job-ID aus der Response lesen und als Prozessvariable zurückgeben

Alle Konfigurationswerte (Client-ID, Secret, Org, Tenant, Folder-ID, Process-Name) kommen aus der `.env` Datei — kein Hardcoding im Code.

### BPMN-Änderung

Der Task wurde von User Task auf Service Task umgestellt:

```xml
<bpmn:serviceTask id="Activity_1e8b8pr" name="Rechnungsdaten im ERP-System eingeben (RPA)">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="uipath-erp-queue" />
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

### Konfiguration (.env)

| Variable | Beschreibung |
|----------|--------------|
| UIPATH_CLIENT_ID | External App Client ID |
| UIPATH_CLIENT_SECRET | External App Client Secret |
| UIPATH_ORG | gruppe11dvg |
| UIPATH_TENANT | DefaultTenant |
| UIPATH_FOLDER_ID | 7919369 (Solution Folder) |
| UIPATH_PROCESS_NAME | RPA Workflow |
| UIPATH_QUEUE_NAME | ERP-Rechnungen |
| UIPATH_POLL_INTERVAL | Wartezeit in Sekunden zwischen Status-Abfragen (Standard: 5) |
| UIPATH_POLL_RETRIES | Maximale Anzahl Status-Abfragen (Standard: 30) |
| UIPATH_JOB_TIMEOUT_MS | Camunda Job-Timeout in ms — muss größer als Poll-Zeit sein (Standard: 180000) |

---

## Fazit

Der Schritt von einem manuellen User Task zu einem vollautomatischen RPA-Bot war der Kern von Sprint 5. Was uns am meisten Zeit gekostet hat, waren die Selektor-Probleme mit den TypeInto-Aktivitäten und die UiPath API-Konfiguration (Robot-Accounts, Folder-Zugang, OAuth2-Scopes).

Am Ende läuft die komplette Kette vollautomatisch: Camunda picked den Task, der Python Worker ruft die UiPath API auf, der Bot startet in der Cloud und trägt die echten Rechnungsdaten aus dem Camunda-Prozess ins ERP-Frontend ein — ohne manuellen Eingriff.
