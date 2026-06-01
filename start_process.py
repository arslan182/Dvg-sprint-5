import os
from pyzeebe import ZeebeClient, create_camunda_cloud_channel
from dotenv import load_dotenv

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")

PROZESS_ID = "Process_1ycjjqr"

SZENARIEN = {
    "1": {
        "name": "Email → automatisch (gRPC + RabbitMQ)",
        "beschreibung": "Rechnung kommt per Email, Metadaten werden automatisch per gRPC gespeichert, Zahlung läuft automatisch über RabbitMQ.",
        "variablen": {
            "eingangskanal": "email",
            "rechnungs_nummer": "R-001",
            "lieferant": "Mustermann GmbH",
            "betrag": 5000,
            "waehrung": "EUR",
            "datum": "2026-06-01",
            "rechnung_genehmigt": True,
            "informationen_erhalten": True,
        }
    },
    "2": {
        "name": "Email → manuell (gRPC Fehler + RabbitMQ Fehler)",
        "beschreibung": "Rechnung kommt per Email, gRPC Server ist nicht erreichbar → Metadaten manuell speichern, RabbitMQ nicht erreichbar → Zahlung manuell erfassen.",
        "variablen": {
            "eingangskanal": "email",
            "rechnungs_nummer": "R-002",
            "lieferant": "Beispiel AG",
            "betrag": 3500,
            "waehrung": "EUR",
            "datum": "2026-06-01",
            "rechnung_genehmigt": True,
            "informationen_erhalten": True,
        }
    },
    "3": {
        "name": "Email → Compliance-Prüfung → Rechnung zurückweisen",
        "beschreibung": "Rechnung kommt per Email, Betrag über Schwellenwert → Compliance manuell prüfen → Sachbearbeiter lehnt ab → Rechnung zurückweisen.",
        "variablen": {
            "eingangskanal": "email",
            "rechnungs_nummer": "R-003",
            "lieferant": "Risiko GmbH",
            "betrag": 15000,
            "waehrung": "EUR",
            "datum": "2026-06-01",
            "rechnung_genehmigt": True,
            "informationen_erhalten": True,
        }
    },
}


def zeige_menu():
    print("\n" + "=" * 55)
    print("  Dvg Sprint 4 – Prozess starten")
    print("=" * 55)
    for key, szenario in SZENARIEN.items():
        print(f"\n  [{key}] {szenario['name']}")
        print(f"      {szenario['beschreibung']}")
    print("\n  [0] Beenden")
    print("=" * 55)


async def main():
    zeige_menu()
    auswahl = input("\nSzenario wählen (0-3): ").strip()

    if auswahl == "0":
        print("Beendet.")
        return

    if auswahl not in SZENARIEN:
        print("Ungültige Auswahl.")
        return

    szenario = SZENARIEN[auswahl]
    print(f"\nStarte: {szenario['name']}")
    print(f"Variablen: {szenario['variablen']}\n")

    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )

    client = ZeebeClient(channel)
    instance = await client.run_process(
        bpmn_process_id=PROZESS_ID,
        variables=szenario["variablen"],
    )

    print(f"Prozess gestartet!")
    print(f"Process Instance Key: {instance.process_instance_key}")
    print(f"Operate: https://operate.camunda.io/{CAMUNDA_CLUSTER_ID}/processes/{instance.process_instance_key}")

    if auswahl == "2":
        print("\nHinweis: Für Szenario 2 müssen server.py und Docker/RabbitMQ NICHT laufen.")
        print("Dann gehen beide Boundary Error Events automatisch in den manuellen Pfad.")
    if auswahl == "3":
        print("\nHinweis: Für Szenario 3 muss in der Tasklist der Task 'Compliance-Fall manuell prüfen'")
        print("geöffnet und 'Ablehnen (Compliance-Verstoß)' gewählt werden.")

    await channel.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
