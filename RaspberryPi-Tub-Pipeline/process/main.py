# process/main.py
# Configure Cassandra to use eventlet event loop (compatible with Python 3.12+)
import eventlet
eventlet.monkey_patch()

import os
import csv
import json
import time
from kafka import KafkaProducer
from cassandra.io.eventletreactor import EventletConnection
from cassandra.cluster import Cluster
from influxdb_client import InfluxDBClient, Point, WritePrecision
from datetime import datetime

# Configurable constants (allow override via env)
KAFKA_TOPIC = "farm_tub_updates"
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CASSANDRA_HOST = os.getenv("CASSANDRA_CONTACT_POINTS", "localhost")
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "adminpass")
INFLUX_ORG = os.getenv("INFLUX_ORG", "iot")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "camera_uptime")

# Setup Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Setup Cassandra
cluster = Cluster([CASSANDRA_HOST], connection_class=EventletConnection)
session = cluster.connect()

# Create keyspaces and tables if not exist
session.execute("""
CREATE KEYSPACE IF NOT EXISTS tub_stats WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 1};
""")

session.execute("""
CREATE KEYSPACE IF NOT EXISTS tub_counts WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 1};
""")

session.set_keyspace('tub_stats')
session.execute("""
CREATE TABLE IF NOT EXISTS farm_tub_stats (
    tub_id text,
    status text,
    timestamp timestamp,
    PRIMARY KEY (tub_id, timestamp)
);
""")

session.set_keyspace('tub_counts')
session.execute("""
CREATE TABLE IF NOT EXISTS farm_tub_counts (
    tub_id text PRIMARY KEY,
    ok_count counter,
    def_count counter
);
""")

# Setup InfluxDB client
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=None)

def validate_tub_data(csv_path: str):
    ok_count = 0
    def_count = 0
    tub_records = []

    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # This validator here assumes CSV has columns: tub_id,status
            # status should be 'ok' or other (defective)
            tub_id = row.get('tub_id') or row.get('tub') or row.get('id')
            status = row.get('status','').lower().strip()
            if status == 'ok':
                ok_count += 1
            else:
                def_count += 1
            tub_records.append({
                'tub_id': tub_id,
                'status': status or 'defective',
                'timestamp': datetime.utcnow().isoformat()
            })
    return {
        'ok': ok_count,
        'defective': def_count,
        'records': tub_records
    }

def process_csv(csv_path: str):
    print(f"[INFO] Processing file: {csv_path}")
    result = validate_tub_data(csv_path)

    for record in result['records']:
        # Insert into Cassandra detailed events (tub_stats keyspace)
        session.set_keyspace('tub_stats')
        try:
            session.execute("""
            INSERT INTO farm_tub_stats (tub_id, status, timestamp) VALUES (%s, %s, toTimestamp(now()))
            """, (record['tub_id'], record['status']))
        except Exception as e:
            print("cassandra insert error (stats):", e)

        # Update counts in Cassandra counters (tub_counts keyspace)
        session.set_keyspace('tub_counts')
        try:
            if record['status'] == 'ok':
                session.execute("UPDATE farm_tub_counts SET ok_count = ok_count + 1 WHERE tub_id = %s", (record['tub_id'],))
            else:
                session.execute("UPDATE farm_tub_counts SET def_count = def_count + 1 WHERE tub_id = %s", (record['tub_id'],))
        except Exception as e:
            print("cassandra counter update error:", e)

        # Send Kafka message for each record
        try:
            producer.send(KAFKA_TOPIC, record)
        except Exception as e:
            print("kafka send error:", e)

    # Write camera uptime metric to InfluxDB (one sample point)
    try:
        point = Point("camera_status").tag("source", "raspi_camera").field("uptime", 1).time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    except Exception as e:
        print("influx write error:", e)

    # flush producer
    try:
        producer.flush(timeout=5)
    except Exception as e:
        print("producer flush error:", e)

    print(f"[INFO] Sent {result['ok']} ok and {result['defective']} defective entries to Kafka.")
    return result

if __name__ == "__main__":
    csv_path = os.getenv("CSV_PATH", "input_data/sample.csv")
    # simple loop: check for file and process every minute
    while True:
        if os.path.exists(csv_path):
            process_csv(csv_path)
            # optional: rotate or remove the file once processed
            try:
                os.remove(csv_path)
            except Exception:
                pass
        else:
            print(f"[WARN] CSV file not found: {csv_path}")
        time.sleep(60)  # Check every minute
