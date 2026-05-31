"""
Sprint 4 - Camunda Job Workers: Automatische Tasks
Lauscht auf:
  - rechnung-erfassen
  - automatische-validierung
  - compliance-check
  - send-request-email
  - rechnung-archivieren
"""

import asyncio
import os
from datetime import datetime
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel

# Camunda SaaS Verbindung
CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID",     "2qwRDM0MDQYft~UA5o_Y27KQl6DhKmOc")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET", "IyGgtDJJ2NmkZR8zdHHO9h.XG6YphoVgGez3cC~LgZni64lqVryMRA84YyW34zTh")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID",    "487e2664-45fe-4a21-9e53-860eddc37e5e")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION",        "bru-2")

# Schwellenwert ab dem Compliance-Prüfung nötig ist
COMPLIANCE_SCHWELLENWERT = float(os.getenv("COMPLIANCE_SCHWELLENWERT", "10000"))


async def rechnung_erfassen(**kwargs):
    """
    Task: rechnung-erfassen
    Erfasst eine eingehende Rechnung und setzt Standardwerte.
    Wird aufgerufen wenn eine neue Rechnung im System eingeht.
    """
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    eingangskanal    = kwargs.get("eingangskanal", "unbekannt")

    print(f"[rechnung-erfassen] Neue Rechnung: {rechnungs_nummer} via {eingangskanal}")

    return {
        "erfassung_zeitstempel": datetime.now().isoformat(),
        "rechnung_status": "erfasst",
    }


async def automatische_validierung(**kwargs):
    """
    Task: automatische-validierung
    Prüft automatisch ob alle Pflichtfelder vorhanden und gültig sind.
    Gibt 'validierung_erfolgreich' zurück (true/false).
    """
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "")
    lieferant        = kwargs.get("lieferant", "")
    betrag           = kwargs.get("betrag", None)
    waehrung         = kwargs.get("waehrung", "")
    datum            = kwargs.get("datum", "")

    print(f"[automatische-validierung] Prüfe Rechnung: {rechnungs_nummer}")

    fehler = []

    if not rechnungs_nummer:
        fehler.append("Rechnungsnummer fehlt")
    if not lieferant:
        fehler.append("Lieferant fehlt")
    if betrag is None or float(betrag) <= 0:
        fehler.append("Betrag ungültig oder fehlt")
    if waehrung not in ("EUR", "USD", "CHF"):
        fehler.append(f"Währung ungültig: {waehrung}")
    if not datum:
        fehler.append("Datum fehlt")

    if fehler:
        print(f"[automatische-validierung] Fehler: {fehler}")
        return {
            "validierung_erfolgreich": False,
            "validierung_fehler": ", ".join(fehler),
        }

    print(f"[automatische-validierung] Rechnung {rechnungs_nummer} erfolgreich validiert.")
    return {
        "validierung_erfolgreich": True,
        "validierung_fehler": "",
    }


async def compliance_check(**kwargs):
    """
    Task: compliance-check
    Prüft automatisch ob eine manuelle Compliance-Prüfung nötig ist.
    Kriterium: Betrag > COMPLIANCE_SCHWELLENWERT (Standard: 10.000 EUR)
    """
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    betrag           = float(kwargs.get("betrag", 0))
    waehrung         = kwargs.get("waehrung", "EUR")

    print(f"[compliance-check] Prüfe Rechnung: {rechnungs_nummer}, Betrag: {betrag} {waehrung}")

    compliance_notwendig = betrag > COMPLIANCE_SCHWELLENWERT

    if compliance_notwendig:
        print(f"[compliance-check] Compliance-Prüfung nötig (Betrag {betrag} > {COMPLIANCE_SCHWELLENWERT})")
    else:
        print(f"[compliance-check] Keine Compliance-Prüfung nötig (Betrag {betrag} <= {COMPLIANCE_SCHWELLENWERT})")

    return {
        "compliance_notwendig": compliance_notwendig,
        "compliance_schwellenwert": COMPLIANCE_SCHWELLENWERT,
    }


async def send_request_email(**kwargs):
    """
    Task: send-request-email
    Sendet eine E-Mail-Anfrage für fehlende Rechnungsinformationen.
    (Simuliert den E-Mail-Versand — kann mit einem SMTP-Service erweitert werden)
    """
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    lieferant        = kwargs.get("lieferant", "Unbekannter Lieferant")
    validierung_fehler = kwargs.get("validierung_fehler", "Fehlende Angaben")

    print(f"[send-request-email] Sende Anfrage an Lieferant '{lieferant}' für Rechnung {rechnungs_nummer}")
    print(f"[send-request-email] Fehlende Informationen: {validierung_fehler}")

    # Hier könnte echter E-Mail-Versand implementiert werden (z.B. smtplib)
    email_inhalt = (
        f"Betreff: Fehlende Informationen zu Rechnung {rechnungs_nummer}\n"
        f"An: {lieferant}\n"
        f"Inhalt: Bitte ergänzen Sie folgende Angaben: {validierung_fehler}"
    )
    print(f"[send-request-email] E-Mail (simuliert):\n{email_inhalt}")

    return {
        "email_gesendet": True,
        "email_zeitstempel": datetime.now().isoformat(),
    }


async def rechnung_archivieren(**kwargs):
    """
    Task: rechnung-archivieren
    Archiviert die abgeschlossene Rechnung.
    """
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    betrag           = kwargs.get("betrag", 0)
    waehrung         = kwargs.get("waehrung", "EUR")

    print(f"[rechnung-archivieren] Archiviere Rechnung: {rechnungs_nummer}, {betrag} {waehrung}")

    return {
        "archiviert": True,
        "archivierungs_zeitstempel": datetime.now().isoformat(),
    }


async def main():
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    worker = ZeebeWorker(channel)

    worker.task(task_type="rechnung-erfassen")(rechnung_erfassen)
    worker.task(task_type="automatische-validierung")(automatische_validierung)
    worker.task(task_type="compliance-check")(compliance_check)
    worker.task(task_type="send-request-email")(send_request_email)
    worker.task(task_type="rechnung-archivieren")(rechnung_archivieren)

    print(f"[Auto Workers] Verbunden mit Camunda SaaS (Cluster: {CAMUNDA_CLUSTER_ID})")
    print("[Auto Workers] Warte auf Jobs:")
    print("  - rechnung-erfassen")
    print("  - automatische-validierung")
    print("  - compliance-check")
    print("  - send-request-email")
    print("  - rechnung-archivieren")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
