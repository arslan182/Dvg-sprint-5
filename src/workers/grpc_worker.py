"""
Sprint 4 - Camunda Job Worker: Metadaten per gRPC speichern
Lauscht auf den Camunda Service Task "save-invoice-metadata"
und ruft den Sprint-2 gRPC Server auf.
"""

import asyncio
import grpc
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel
from pyzeebe.errors import BusinessError

# Sprint-2 gRPC imports (Pfad relativ zum Projektroot)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from invoice_metadata import invoice_pb2
from invoice_metadata import invoice_pb2_grpc

# Camunda SaaS Verbindung
CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID",     "2qwRDM0MDQYft~UA5o_Y27KQl6DhKmOc")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET", "IyGgtDJJ2NmkZR8zdHHO9h.XG6YphoVgGez3cC~LgZni64lqVryMRA84YyW34zTh")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID",    "487e2664-45fe-4a21-9e53-860eddc37e5e")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION",        "bru-2")

# gRPC Server Adresse (Sprint-2)
GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = int(os.getenv("GRPC_PORT", 50051))


async def save_metadata(
    rechnungs_nummer: str,
    lieferant: str,
    betrag: float,
    waehrung: str,
    datum: str,
):
    """
    Wird von Camunda aufgerufen wenn der Service Task 'save-invoice-metadata' erreicht wird.
    Variablen kommen aus dem Camunda Prozess (Formular-Eingaben oder Prozessvariablen).
    """
    print(f"[gRPC Worker] Speichere Metadaten für Rechnung: {rechnungs_nummer}")

    try:
        channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
        stub = invoice_pb2_grpc.RechnungServiceStub(channel)

        request = invoice_pb2.RechnungRequest(
            rechnungs_nummer=rechnungs_nummer,
            lieferant=lieferant,
            betrag=float(betrag),
            waehrung=waehrung,
            datum=datum,
            status=invoice_pb2.OFFEN
        )

        response = stub.SpeichereMetadaten(request)

        if response.erfolg:
            print(f"[gRPC Worker] Erfolgreich gespeichert: {response.nachricht}")
            # Rückgabe an Camunda Prozess
            return {"grpc_erfolg": True, "grpc_nachricht": response.nachricht}
        else:
            print(f"[gRPC Worker] Fehler vom Server: {response.nachricht}")
            raise Exception(f"gRPC Server Fehler: {response.nachricht}")

    except grpc.RpcError as e:
        print(f"[gRPC Worker] gRPC Server nicht erreichbar: {e.details()}")
        raise BusinessError(error_code="grpc-fehler", msg=f"gRPC nicht erreichbar: {e.details()}")

    finally:
        channel.close()


async def main():
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    worker = ZeebeWorker(channel)

    # Task-Type muss mit dem Service Task im BPMN übereinstimmen!
    worker.task(task_type="save-invoice-metadata")(save_metadata)

    print(f"[gRPC Worker] Verbunden mit Camunda SaaS (Cluster: {CAMUNDA_CLUSTER_ID})")
    print("[gRPC Worker] Warte auf Jobs vom Task-Typ 'save-invoice-metadata'...")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
