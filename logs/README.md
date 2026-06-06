# Terminal Logs – Sprint 5

Hier sind die Terminal-Ausgaben der Worker und des Servers gespeichert. Die Logs zeigen den kompletten Ablauf eines Testlaufs.

## Dateien

| Datei | Inhalt |
|-------|--------|
| `server.log` | Ausgabe von invoice_metadata/server.py (gRPC Server) |
| `auto_workers.log` | Ausgabe von auto_workers.py (rechnung-erfassen, validierung, compliance-check, etc.) |
| `grpc_worker.log` | Ausgabe von grpc_worker.py (Metadaten per gRPC speichern) |
| `payment_worker.log` | Ausgabe von payment_worker.py (Zahlungsauftrag per RabbitMQ) |
| `start_process.log` | Ausgabe von start_process.py (Prozess starten) |
| `tests.log` | Ausgabe der Unit Tests (pytest) |
| `camunda_operate_screenshot.png` | Screenshot aus Camunda Operate während des Testlaufs |

> **Hinweis:** Docker-Logs werden nicht als Datei gespeichert. Docker schreibt intern seine eigenen Logs, die man mit `docker logs <container-name>` abrufen kann.

## Log erzeugen

```powershell
# Docker (Hintergrund, keine Log-Datei nötig)
docker-compose up -d

# gRPC Server
& "...\python.exe" -m src.invoice_metadata.server *>&1 | Tee-Object -FilePath logs/server.log

# Auto Workers
& "...\python.exe" src/workers/auto_workers.py *>&1 | Tee-Object -FilePath logs/auto_workers.log

# gRPC Worker
& "...\python.exe" src/workers/grpc_worker.py *>&1 | Tee-Object -FilePath logs/grpc_worker.log

# Payment Worker
& "...\python.exe" src/workers/payment_worker.py *>&1 | Tee-Object -FilePath logs/payment_worker.log

# Prozess starten
& "...\python.exe" start_process.py *>&1 | Tee-Object -FilePath logs/start_process.log

# Unit Tests
$env:PYTHONPATH = "."; & "...\pytest.exe" tests/test_workers.py -v *>&1 | Tee-Object -FilePath logs/tests.log
```
