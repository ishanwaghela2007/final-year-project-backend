# RaspberryPi-Tub-Pipeline

Lightweight pipeline for validating "farma tubs" from CSV, streaming defects via Kafka, storing detailed events in Cassandra and uptime in InfluxDB, plus a FastAPI server exposing REST and WebSocket and a monthly emitter.

## Quick start
1. Setup Kafka / InfluxDB / Cassandra (remote recommended on Raspberry Pi).
2. Edit `config.py` (or set env vars) to point to your services.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run API (and websocket bridge): `./run_api.sh`.
5. Process a CSV: `./run_main.sh /path/to/file.csv`.
6. Emit monthly summary: `./run_emitter.sh` (or schedule with cron).

## Tests
`pytest`