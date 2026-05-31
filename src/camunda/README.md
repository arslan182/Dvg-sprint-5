# Camunda Sprint 4

## Ordnerstruktur

```
src/camunda/
├── forms/
│   ├── invoice_form.json     # Formular: Rechnungsdaten manuell erfassen
│   └── compliance_form.json  # Formular: Compliance-Fall manuell prüfen
└── README.md
```

## Formulare in Camunda einbinden

1. Camunda Modeler öffnen
2. "New Form" → jeweilige JSON-Datei importieren
3. Im BPMN den User Task auswählen → "Form" Tab → Form verknüpfen

## Prozessvariablen

Die Worker erwarten folgende Variablen im Prozess:

| Variable           | Typ    | Beschreibung              |
|--------------------|--------|---------------------------|
| rechnungs_nummer   | String | Eindeutige Rechnungsnummer|
| lieferant          | String | Name des Lieferanten      |
| betrag             | Number | Rechnungsbetrag           |
| waehrung           | String | EUR / USD / CHF           |
| datum              | String | Datum im Format YYYY-MM-DD|
| eingangskanal      | String | email / portal / edi      |

## Service Task Typen (im BPMN eintragen)

| BPMN Task                    | Task-Typ               |
|------------------------------|------------------------|
| Metadaten per gRPC speichern | save-invoice-metadata  |
| Zahlung veranlassen          | initiate-payment       |
