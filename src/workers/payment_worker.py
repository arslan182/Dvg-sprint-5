"""
Sprint 4 - Camunda Job Worker: Zahlung veranlassen
Lauscht auf den Camunda Service Task "initiate-payment"
und schickt eine Nachricht an RabbitMQ (zahlungs_auftraege Queue).
"""

import asyncio
import json
import pika
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel
from pyzeebe.errors import BusinessError
import os

# Camunda SaaS Verbindung
CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID",     "2qwRDM0MDQYft~UA5o_Y27KQl6DhKmOc")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET", "IyGgtDJJ2NmkZR8zdHHO9h.XG6YphoVgGez3cC~LgZni64lqVryMRA84YyW34zTh")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID",    "487e2664-45fe-4a21-9e53-860eddc37e5e")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION",        "bru-2")

# RabbitMQ Verbindung (Sprint-2)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")


async def initiate_payment(
    rechnungs_nummer: str,
    betrag: float,
    waehrung: str,
):
    """
    Wird von Camunda aufgerufen wenn der Service Task 'initiate-payment' erreicht wird.
    Schickt einen Zahlungsauftrag an RabbitMQ (wie Sprint-2 client.py).
    """
    print(f"[Payment Worker] Veranlasse Zahlung für Rechnung: {rechnungs_nummer}")

    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                credentials=credentials
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue="zahlungs_auftraege", durable=True)

        zahlungs_daten = {
            "rechnungsnummer": rechnungs_nummer,
            "betrag": float(betrag),
            "waehrung": waehrung
        }

        channel.basic_publish(
            exchange="",
            routing_key="zahlungs_auftraege",
            body=json.dumps(zahlungs_daten),
            properties=pika.BasicProperties(delivery_mode=2)  # persistent
        )

        connection.close()

        print(f"[Payment Worker] Zahlungsauftrag für {rechnungs_nummer} an RabbitMQ gesendet.")
        return {"zahlung_erfolg": True, "zahlung_nachricht": f"Zahlungsauftrag für {rechnungs_nummer} gesendet"}

    except Exception as e:
        print(f"[Payment Worker] Fehler beim Senden an RabbitMQ: {e}")
        raise BusinessError(error_code="rabbitmq-fehler", msg=f"RabbitMQ nicht erreichbar: {e}")


async def main():
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    worker = ZeebeWorker(channel)

    # Task-Type muss mit dem Service Task im BPMN übereinstimmen!
    worker.task(task_type="initiate-payment")(initiate_payment)

    print(f"[Payment Worker] Verbunden mit Camunda SaaS (Cluster: {CAMUNDA_CLUSTER_ID})")
    print("[Payment Worker] Warte auf Jobs vom Task-Typ 'initiate-payment'...")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
