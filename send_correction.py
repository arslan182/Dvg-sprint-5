import os
import sys
import asyncio
from pyzeebe import ZeebeClient, create_camunda_cloud_channel
from dotenv import load_dotenv

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")


async def main():
    if len(sys.argv) < 2:
        print("Verwendung: python send_correction.py <rechnungs_nummer>")
        print("Beispiel:   python send_correction.py R-001")
        return

    rechnungs_nummer = sys.argv[1]

    print(f"Sende Korrektur-Nachricht für Rechnung: {rechnungs_nummer}")

    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )

    client = ZeebeClient(channel)

    await client.publish_message(
        name="Message_2ae8oeh",
        correlation_key=rechnungs_nummer,
        variables={
            "informationen_erhalten": True,
            "korrektur_zeitstempel": __import__("datetime").datetime.now().isoformat(),
        },
    )

    print(f"Nachricht gesendet. Prozess für {rechnungs_nummer} läuft weiter.")
    await channel.close()


if __name__ == "__main__":
    asyncio.run(main())
