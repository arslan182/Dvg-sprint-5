# Sprint 5 – Testdokumentation RPA Bot
**Hochschule Karlsruhe** | Modul: Digitalisierung von Geschäftsprozessen | Gruppe G11

---

## 5.1 Implementierung

### Ziel
Automatisierung der Erfassung von Rechnungsdaten in das ERP-Frontend mittels UiPath RPA Bot.

### Technologie
- **Tool:** UiPath Studio Web
- **Browser:** Microsoft Edge
- **Ziel-URL:** https://arslan182.github.io/Dvg-sprint-5/erp_frontend.html
- **Automatisierungsansatz:** JavaScript Injection via „Inject Js Script" Aktivität

### Workflow-Aufbau

```
Manual Trigger
└── Use Browser Edge: ERP-System – Rechnungserfassung
    ├── Assign: in_rechnungs_nummer = "RE-2026-00042"
    ├── Assign: in_lieferant = "Mustermann GmbH"
    ├── Assign: in_betrag = "5500"
    └── Inject Js Script (Ziel: Formular "Neue Rechnung erfassen")
        → Befüllt alle Felder per getElementById
        → Klickt "Rechnung speichern"
```

### Implementierungsdetails

Der Bot verwendet JavaScript Injection, um die HTML-Formularfelder direkt über ihre `id`-Attribute anzusprechen. Dieser Ansatz wurde gewählt, da die Standard-TypeInto-Aktivitäten bei cloud-gehosteten Seiten zu Selektor-Instabilität führten (Healing Agent Timeout). JavaScript Injection ist eine anerkannte RPA-Technik für webbasierte Automatisierungen.

**Befüllte Felder:**

| Feld | HTML-ID | Testwert |
|------|---------|----------|
| Rechnungsnummer | `rechnungs_nummer` | RE-2026-00042 |
| Lieferant | `lieferant` | Mustermann GmbH |
| Rechnungsdatum | `datum` | 05.06.2026 (Default) |
| Eingangskanal | `eingangskanal` | Email |
| Betrag | `betrag` | 5500 |
| Währung | `waehrung` | EUR |
| Status | `status` | OFFEN |
| Bemerkung | `bemerkung` | Automatisch erfasst via RPA Bot |

---

## 5.2 Testergebnisse

### Testfall 1 – Erfolgreiche Formularerfassung

| Attribut | Wert |
|----------|------|
| **Datum** | 05.06.2026 |
| **Uhrzeit** | 17:46:23 – 17:46:36 CEST |
| **Ergebnis** | ✅ Erfolgreich |
| **Ausführungszeit** | ~5 Sekunden |

**Ausführungslog:**

```
17:46:23  Preparing projects for debugging... completed
17:46:26  Packages restored
17:46:30  Building project completed
17:46:31  RPA Workflow execution started
17:46:32  Using Web App. Browser: Edge URL: https://arslan182.github.io/Dvg-sprint-5/erp_frontend.html
17:46:32  Healing agent configuration.
17:46:36  RPA Workflow execution ended
```

**Aktivitätsstatus:**

| Aktivität | Status |
|-----------|--------|
| Manual Trigger | ✅ Successful |
| Use Browser Edge: ERP-System – Rechnungserfassung | ✅ Successful |
| Inject Js Script 'Neue Rechnung erfassen ...' | ✅ Successful |
| Assign in_rechnungs_nummer | ✅ Successful |
| Assign in_lieferant | ✅ Successful |
| Assign in_betrag | ✅ Successful |

### Beobachtungen

- Der Bot öffnet die GitHub Pages URL zuverlässig in Microsoft Edge
- Die Felder werden per JavaScript korrekt befüllt
- Der Submit-Button wird automatisch geklickt
- Gesamtlaufzeit: ca. 5 Sekunden

### Bekannte Einschränkungen

- Der Bot läuft als **Unattended Bot** in der UiPath Cloud — das Ergebnis ist nur im UiPath Live Stream oder den Aktivitäts-Vorschaubildern sichtbar, nicht im lokalen Browser
- TypeInto-Aktivitäten wurden durch JavaScript Injection ersetzt, da die Selektoren bei der cloud-gehosteten Seite instabil waren

---

## Fazit

Der RPA Bot (Aufgabe 5.1) wurde erfolgreich implementiert und getestet (Aufgabe 5.2). Die Automatisierung der Rechnungserfassung im ERP-Frontend funktioniert vollständig: Der Bot öffnet die Webanwendung, befüllt alle relevanten Formularfelder mit den Rechnungsdaten und speichert den Eintrag automatisch — ohne manuelle Interaktion.
