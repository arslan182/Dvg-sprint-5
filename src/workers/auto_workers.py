import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel
import httpx

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")

UIPATH_CLIENT_ID     = os.getenv("UIPATH_CLIENT_ID")
UIPATH_CLIENT_SECRET = os.getenv("UIPATH_CLIENT_SECRET")
UIPATH_ORG           = os.getenv("UIPATH_ORG")
UIPATH_TENANT        = os.getenv("UIPATH_TENANT")
UIPATH_FOLDER_ID     = os.getenv("UIPATH_FOLDER_ID")
UIPATH_QUEUE_NAME    = os.getenv("UIPATH_QUEUE_NAME")
UIPATH_PROCESS_NAME  = os.getenv("UIPATH_PROCESS_NAME", "RPA Workflow")
UIPATH_POLL_INTERVAL  = int(os.getenv("UIPATH_POLL_INTERVAL", "5"))
UIPATH_POLL_RETRIES   = int(os.getenv("UIPATH_POLL_RETRIES", "30"))
UIPATH_JOB_TIMEOUT_MS = int(os.getenv("UIPATH_JOB_TIMEOUT_MS", "180000"))


async def rechnung_erfassen(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    eingangskanal    = kwargs.get("eingangskanal", "unbekannt")

    print(f"[rechnung-erfassen] {rechnungs_nummer} via {eingangskanal}")

    return {
        "erfassung_zeitstempel": datetime.now().isoformat(),
        "rechnung_status": "erfasst",
    }


async def automatische_validierung(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "")
    lieferant        = kwargs.get("lieferant", "")
    betrag           = kwargs.get("betrag", None)
    waehrung         = kwargs.get("waehrung", "")
    datum            = kwargs.get("datum", "")

    print(f"[automatische-validierung] Prüfe: {rechnungs_nummer}")

    fehler = []

    if not rechnungs_nummer:
        fehler.append("Rechnungsnummer fehlt")
    if not lieferant:
        fehler.append("Lieferant fehlt")
    if betrag is None or float(betrag) <= 0:
        fehler.append("Betrag ungültig oder fehlt")
    if waehrung not in ("EUR", "USD", "CHF", "GBP"):
        fehler.append(f"Währung ungültig: {waehrung}")
    if not datum:
        fehler.append("Datum fehlt")

    if fehler:
        print(f"[automatische-validierung] Fehler: {fehler}")
        return {
            "validierung_erfolgreich": False,
            "validierung_fehler": ", ".join(fehler),
        }

    print(f"[automatische-validierung] {rechnungs_nummer} OK")
    return {
        "validierung_erfolgreich": True,
        "validierung_fehler": "",
    }


async def compliance_check(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    betrag           = float(kwargs.get("betrag", 0))
    waehrung         = kwargs.get("waehrung", "EUR").upper()

    schwellenwerte = {
        "EUR": 10000,
        "USD": 11000,
        "CHF": 10800,
        "GBP": 8700,
    }

    schwellenwert        = schwellenwerte.get(waehrung, 10000)
    compliance_notwendig = betrag > schwellenwert

    print(f"[compliance-check] {rechnungs_nummer}: {betrag} {waehrung} (Schwellenwert: {schwellenwert})")

    return {
        "compliance_notwendig": compliance_notwendig,
        "compliance_schwellenwert": schwellenwert,
    }


async def send_request_email(**kwargs):
    rechnungs_nummer   = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    lieferant          = kwargs.get("lieferant", "Unbekannter Lieferant")
    validierung_fehler = kwargs.get("validierung_fehler", "Fehlende Angaben")

    print(f"[send-request-email] Anfrage an '{lieferant}' für {rechnungs_nummer}")
    print(f"[send-request-email] Fehlende Infos: {validierung_fehler}")

    return {
        "email_gesendet": True,
        "email_zeitstempel": datetime.now().isoformat(),
    }


async def uipath_erp_queue(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    lieferant        = kwargs.get("lieferant", "Unbekannt")
    betrag           = str(kwargs.get("betrag", "0"))
    waehrung         = kwargs.get("waehrung", "EUR")
    eingangskanal    = kwargs.get("eingangskanal", "Email")

    print(f"[uipath-erp-queue] Starte für Rechnung {rechnungs_nummer}")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        token_resp = await client.post(
            f"https://cloud.uipath.com/{UIPATH_ORG}/identity_/connect/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     UIPATH_CLIENT_ID,
                "client_secret": UIPATH_CLIENT_SECRET,
                "scope":         "OR.Jobs OR.Jobs.Write OR.Execution OR.Execution.Write OR.Queues OR.Queues.Read OR.Queues.Write",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
        print(f"[uipath-erp-queue] Token erhalten")

        start_resp = await client.post(
            f"https://cloud.uipath.com/{UIPATH_ORG}/{UIPATH_TENANT}/orchestrator_/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs",
            headers={
                "Authorization":                f"Bearer {access_token}",
                "Content-Type":                 "application/json",
                "X-UIPATH-OrganizationUnitId":  str(UIPATH_FOLDER_ID),
            },
            json={
                "startInfo": {
                    "ReleaseName":    UIPATH_PROCESS_NAME,
                    "Strategy":       "ModernJobsCount",
                    "JobsCount":      1,
                    "Source":         "Manual",
                    "InputArguments": json.dumps({
                        "rechnungs_nummer": rechnungs_nummer,
                        "lieferant":        lieferant,
                        "betrag":           betrag,
                        "waehrung":         waehrung,
                        "eingangskanal":    eingangskanal,
                    }),
                }
            },
        )
        print(f"[uipath-erp-queue] StartJobs: {start_resp.status_code} {start_resp.text[:300]}")
        start_resp.raise_for_status()
        item_id = start_resp.json().get("value", [{}])[0].get("Id", "gestartet")
        print(f"[uipath-erp-queue] Job gestartet, ID: {item_id}")

        for _ in range(UIPATH_POLL_RETRIES):
            await asyncio.sleep(UIPATH_POLL_INTERVAL)
            status_resp = await client.get(
                f"https://cloud.uipath.com/{UIPATH_ORG}/{UIPATH_TENANT}/orchestrator_/odata/Jobs({item_id})",
                headers={
                    "Authorization":               f"Bearer {access_token}",
                    "X-UIPATH-OrganizationUnitId": str(UIPATH_FOLDER_ID),
                },
            )
            if status_resp.status_code == 200:
                state = status_resp.json().get("State", "")
                print(f"[uipath-erp-queue] Job Status: {state}")
                if state == "Successful":
                    print(f"[uipath-erp-queue] Bot erfolgreich abgeschlossen.")
                    break
                if state in ("Faulted", "Stopped"):
                    raise Exception(f"UiPath Job fehlgeschlagen: {state}")

    return {
        "uipath_queue_item_id": item_id,
        "uipath_queue_zeitstempel": datetime.now().isoformat(),
        "uipath_job_status": "Successful",
    }


async def rechnung_archivieren(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    betrag           = kwargs.get("betrag", 0)
    waehrung         = kwargs.get("waehrung", "EUR")

    print(f"[rechnung-archivieren] {rechnungs_nummer}, {betrag} {waehrung}")

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
    worker.task(task_type="uipath-erp-queue", timeout_ms=UIPATH_JOB_TIMEOUT_MS)(uipath_erp_queue)

    print(f"[Auto Workers] Cluster: {CAMUNDA_CLUSTER_ID}")
    print("[Auto Workers] Wartet auf Jobs...")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
