# fastapi_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cassandra.cluster import Cluster
import datetime, uuid

CASSANDRA_CONTACT_POINTS = ["<<REPLACE_ME_CASSANDRA_HOST>>"]
KEYSPACE = "tube_factory"

cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS)
session = cluster.connect()
session.execute(f"CREATE KEYSPACE IF NOT EXISTS {KEYSPACE} WITH replication = {{'class':'SimpleStrategy','replication_factor':1}}")
session.set_keyspace(KEYSPACE)

# Ensure tables (idempotent)
session.execute("""
CREATE TABLE IF NOT EXISTS inspection_results (
    batch_id text,
    ts timestamp,
    report_id uuid,
    produced_count int,
    scratch int,
    crack int,
    bend int,
    hole int,
    PRIMARY KEY (batch_id, ts)
) WITH CLUSTERING ORDER BY (ts DESC);
""")

session.execute("""
CREATE TABLE IF NOT EXISTS batch_status (
    batch_id text PRIMARY KEY,
    produced_count int,
    scratch int,
    crack int,
    bend int,
    hole int,
    target int
);
""")

app = FastAPI()

class CountsItem(BaseModel):
    batch: str
    counts: int
    defects: dict
    report_id: str | None = None

@app.post("/add_inspection")
def add_inspection(item: CountsItem):
    try:
        rid = uuid.UUID(item.report_id) if item.report_id else uuid.uuid4()
    except Exception:
        raise HTTPException(400, "report_id invalid")

    now = datetime.datetime.utcnow()
    scratch = int(item.defects.get("scratch", 0))
    crack = int(item.defects.get("crack", 0))
    bend = int(item.defects.get("bend", 0))
    hole = int(item.defects.get("hole", 0))
    produced = int(item.counts)

    session.execute(
        "INSERT INTO inspection_results (batch_id, ts, report_id, produced_count, scratch, crack, bend, hole) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (item.batch, now, rid, produced, scratch, crack, bend, hole)
    )

    # upsert summary in batch_status
    row = session.execute("SELECT produced_count, scratch, crack, bend, hole FROM batch_status WHERE batch_id=%s", (item.batch,)).one()
    if row:
        p = (row.produced_count or 0) + produced
        s = (row.scratch or 0) + scratch
        c = (row.crack or 0) + crack
        b = (row.bend or 0) + bend
        h = (row.hole or 0) + hole
        session.execute("UPDATE batch_status SET produced_count=%s, scratch=%s, crack=%s, bend=%s, hole=%s WHERE batch_id=%s",
                        (p, s, c, b, h, item.batch))
    else:
        session.execute("INSERT INTO batch_status (batch_id, produced_count, scratch, crack, bend, hole, target) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (item.batch, produced, scratch, crack, bend, hole, 0))

    return {"status":"ok", "batch": item.batch}

@app.get("/batch_status/{batch_id}")
def get_status(batch_id: str):
    row = session.execute("SELECT produced_count, scratch, crack, bend, hole, target FROM batch_status WHERE batch_id=%s", (batch_id,)).one()
    if not row:
        raise HTTPException(404, "batch not found")
    return {
        "batch_id": batch_id,
        "produced": row.produced_count,
        "scratch": row.scratch,
        "crack": row.crack,
        "bend": row.bend,
        "hole": row.hole,
        "target": row.target
    }
