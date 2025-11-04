# process/storages.py
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from cassandra.cluster import Cluster
from config import (
    INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET,
    CASSANDRA_CONTACT_POINTS, CASSANDRA_KEYSPACE_EVENTS, CASSANDRA_KEYSPACE_STATS
)

class InfluxWriter:
    def __init__(self):
        try:
            self.client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
            self.write_api = self.client.write_api()
        except Exception as e:
            print("Influx init error:", e)
            self.client = None
            self.write_api = None

    def write_uptime(self, camera_id: str, ts_unix_s: int, uptime_seconds:int):
        if not self.write_api:
            return
        try:
            p = Point("camera_uptime").tag("camera_id", camera_id).field("uptime_seconds", int(uptime_seconds)).time(ts_unix_s, WritePrecision.S)
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
        except Exception as e:
            print("influx write error:", e)


class CassandraWriter:
    def __init__(self):
        self.cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS)
        self.session = self.cluster.connect()
        # keyspace for detailed events
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE_EVENTS}
            WITH replication = {{ 'class':'SimpleStrategy', 'replication_factor': '1' }}
        """)
        self.session.set_keyspace(CASSANDRA_KEYSPACE_EVENTS)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS tub_events (
                camera_id text,
                tub_id text,
                timestamp text,
                is_defective boolean,
                defects list<text>,
                other_meta text,
                PRIMARY KEY ((camera_id), timestamp, tub_id)
            )
        """)
        self.insert_stmt = self.session.prepare("""
            INSERT INTO tub_events (camera_id,tub_id,timestamp,is_defective,defects,other_meta)
            VALUES (?, ?, ?, ?, ?, ?)
        """)

    def insert_event(self, camera_id, tub_id, timestamp, is_defective, defects, other_meta):
        try:
            self.session.execute(self.insert_stmt, (camera_id, tub_id, timestamp, is_defective, defects, other_meta))
        except Exception as e:
            print("cassandra insert error:", e)


class StatsWriter:
    def __init__(self):
        self.cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS)
        self.session = self.cluster.connect()
        # create stats keyspace
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE_STATS}
            WITH replication = {{ 'class':'SimpleStrategy', 'replication_factor': '1' }}
        """)
        self.session.set_keyspace(CASSANDRA_KEYSPACE_STATS)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS tub_counts (
                camera_id text,
                date text,
                total_count counter,
                defective_count counter,
                PRIMARY KEY ((camera_id), date)
            )
        """)
        self.inc_total = self.session.prepare(
            "UPDATE tub_counts SET total_count = total_count + 1 WHERE camera_id=? AND date=?"
        )
        self.inc_defect = self.session.prepare(
            "UPDATE tub_counts SET defective_count = defective_count + 1 WHERE camera_id=? AND date=?"
        )

    def update_counts(self, camera_id:str, is_defective:bool):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        try:
            self.session.execute(self.inc_total, (camera_id, today))
            if is_defective:
                self.session.execute(self.inc_defect, (camera_id, today))
        except Exception as e:
            print("stats update error:", e)
