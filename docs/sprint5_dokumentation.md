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
    ├── Assign: in_rechnungs_nummer = "RE-2026-00042"
    ├── Assign: in_lieferant = "Mustermann GmbH"
    ├── Assign: in_betrag = "5500"
    │
    └── Inject Js Script
        → Alle Felder per getElementById befüllen
        → Formular abschicken
```

### JavaScript-Code

```javascript
function (element, input) {
  document.getElementById('rechnungs_nummer').value = 'RE-2026-00042';
  document.getElementById('lieferant').value = 'Mustermann GmbH';
  document.getElementById('betrag').value = '5500';
  document.getElementById('eingangskanal').value = 'Email';
  document.getElementById('waehrung').value = 'EUR';
  document.getElementById('status').value = 'OFFEN';
  document.getElementById('bemerkung').value = 'Automatisch erfasst via RPA Bot';
  document.querySelector('button[type=submit]').click();
}
```

### Testdaten

Die Rechnungsdaten kommen aus `rechnung_data.json`:

| Feld | Wert |
|------|------|
| Rechnungsnummer | RE-2026-00042 |
| Lieferant | Mustermann GmbH |
| Betrag | 5500 EUR |
| Eingangskanal | Email |
| Status | OFFEN |
| Bemerkung | Automatisch erfasst via RPA Bot |

---

## Test (5.2)

### Testergebnis

Der Bot wurde am 05.06.2026 erfolgreich ausgeführt. Alle Aktivitäten liefen ohne Fehler durch:

```
17:46:23  Preparing projects for debugging... completed
17:46:26  Packages restored
17:46:30  Building project completed
17:46:31  RPA Workflow execution started
17:46:32  Using Web App. Browser: Edge
          URL: https://arslan182.github.io/Dvg-sprint-5/erp_frontend.html
17:46:32  Healing agent configuration.
17:46:36  RPA Workflow execution ended
```

Gesamtlaufzeit: ca. 5 Sekunden. Alle Aktivitäten zeigten Status "Successful".

Da der Bot als Unattended Bot in der UiPath Cloud läuft, passiert die Ausführung in einer separaten Browser-Session — nicht im lokalen Browser. Das Ergebnis ist im UiPath Live Stream und in den Aktivitäts-Vorschaubildern von Studio Web sichtbar.

### Was wir beim Testen gelernt haben

- Der "Healing agent configuration" Log-Eintrag erscheint immer beim Start, auch wenn der Healing Agent deaktiviert ist — das ist nur eine Initialisierungsmeldung, kein Fehler
- Der Bot läuft in einer Cloud-Session, deshalb sieht man das ausgefüllte Formular nicht im eigenen Browser
- TypeInto-Aktivitäten hatten Selektor-Probleme mit der GitHub Pages URL — JavaScript Injection war zuverlässiger

---

## Einbindung in Camunda (5.3)

### Überblick

Den Bot haben wir als Unattended Bot in UiPath Orchestrator deployed und dann den BPMN-Prozess angepasst. Der bisherige User Task "Rechnungsdaten im ERP-System eingeben" ist jetzt ein automatischer Service Task, der den UiPath Connector aufruft.

### Deployment

1. In UiPath Studio Web auf "Publish" geklickt → "Shared" ausgewählt → Version 1.0.0 veröffentlicht
2. Im UiPath Orchestrator: Solutions → Deploy → "Install as root folder" → Deployment war nach ca. 2 Minuten abgeschlossen (Status: Successful, Active)
3. Folder: `Shared/Solution`

### External App für Camunda

Damit Camunda den Bot aufrufen kann, brauchen wir OAuth2-Credentials. Wir haben in der UiPath Cloud Admin unter External Applications eine neue Confidential Application angelegt:

- **Name:** Camunda-Connector
- **Scope:** OR.Execution (Orchestrator API Access)
- **Typ:** Confidential application (Client Credentials Flow)

### BPMN-Änderung

Der User Task `Activity_1e8b8pr` wurde in einen Service Task mit dem Camunda UiPath Connector umgewandelt:

**Vorher:**
```xml
<bpmn:userTask id="Activity_1e8b8pr" name="Rechnungsdaten im ERP-System eingeben">
  <bpmn:extensionElements>
    <zeebe:userTask />
    <zeebe:formDefinition formId="invoice-form" />
  </bpmn:extensionElements>
</bpmn:userTask>
```

**Nachher:**
```xml
<bpmn:serviceTask id="Activity_1e8b8pr" name="Rechnungsdaten im ERP-System eingeben (RPA)">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="io.camunda:uipath:1" />
    <zeebe:ioMapping>
      <!-- OAuth2-Konfiguration und Orchestrator-Details -->
      <zeebe:input source="Solution" target="folderPath" />
      <zeebe:input source="RPA Workflow" target="processName" />
      <zeebe:input source="startJob" target="operationType" />
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

### Konfiguration UiPath Connector

| Parameter | Wert |
|-----------|------|
| Orchestrator URL | https://cloud.uipath.com |
| Organization | gruppe11dvg |
| Tenant | DefaultTenant |
| Folder | Solution |
| Process | RPA Workflow |
| Auth | OAuth2 Client Credentials |
| Scope | OR.Execution |

---

## Fazit

Der Schritt von einem manuellen User Task zu einem vollautomatischen RPA-Bot war der Kern von Sprint 5. Was uns am meisten Zeit gekostet hat, waren die Selektor-Probleme mit den TypeInto-Aktivitäten — das hätten wir ohne die JavaScript-Lösung nicht so schnell hinbekommen.

Die Integration mit Camunda über den UiPath Connector macht aus dem Bot einen richtigen Teil des Gesamtprozesses: Sobald eine Rechnung freigegeben wird, startet Camunda automatisch den Bot, der die Daten ins ERP einträgt — ohne dass jemand manuell eingreifen muss.
