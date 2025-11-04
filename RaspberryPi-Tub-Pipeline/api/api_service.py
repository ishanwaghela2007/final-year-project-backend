# api/api_service.py
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer
from threading import Thread
from config import (
    API_HOST, API_PORT, CASSANDRA_CONTACT_POINTS, CASSANDRA_KEYSPACE_STATS,
    KAFKA_BOOTSTRAP, KAFKA_WEBSOCKET_TOPIC
)

app = FastAPI(title="Tub Stats API")

# Cassandra session (stats keyspace) - lazy load
session = None

def get_cassandra_session():
    global session
    if session is None:
        # Configure Cassandra for Python 3.13+
        import os
        os.environ['CASSANDRA_EVENT_LOOP'] = 'eventlet'
        from cassandra.cluster import Cluster
        from cassandra.io.eventletreactor import EventletConnection
        cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, connection_class=EventletConnection)
        session = cluster.connect()
        session.set_keyspace(CASSANDRA_KEYSPACE_STATS)
    return session

# WebSocket clients
clients = set()
clients_lock = asyncio.Lock()

async def broadcast(data):
    to_remove = []
    async with clients_lock:
        for ws in list(clients):
            try:
                await ws.send_json(data)
            except Exception:
                to_remove.append(ws)
        for r in to_remove:
            clients.remove(r)

def kafka_consumer_loop():
    consumer = KafkaConsumer(
        KAFKA_WEBSOCKET_TOPIC,
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='latest',
        consumer_timeout_ms=1000
    )
    for message in consumer:
        data = message.value
        try:
            asyncio.get_event_loop().create_task(broadcast(data))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(broadcast(data))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with clients_lock:
        clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        async with clients_lock:
            if websocket in clients:
                clients.remove(websocket)

@app.get("/stats/{camera_id}")
async def get_camera_stats(camera_id: str):
    from datetime import datetime
    sess = get_cassandra_session()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    q = "SELECT total_count, defective_count FROM tub_counts WHERE camera_id=%s AND date=%s"
    try:
        row = sess.execute(q, (camera_id, today)).one()
    except Exception:
        return {"camera_id": camera_id, "date": today, "total_count": 0, "defective_count": 0, "defect_rate": 0}
    if not row:
        return {"camera_id": camera_id, "date": today, "total_count": 0, "defective_count": 0, "defect_rate": 0}
    total = row.total_count or 0
    defect = row.defective_count or 0
    rate = (defect / total * 100) if total > 0 else 0
    return {"camera_id": camera_id, "date": today, "total_count": total, "defective_count": defect, "defect_rate": round(rate, 2)}

def start_kafka_thread():
    t = Thread(target=kafka_consumer_loop, daemon=True)
    t.start()

if __name__ == "__main__":
    start_kafka_thread()
    import uvicorn
    uvicorn.run("api.api_service:app", host=API_HOST, port=API_PORT, log_level="info", workers=1)
