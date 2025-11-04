# emitter/monthly_emitter.py
import json
from datetime import datetime
from cassandra.cluster import Cluster
from kafka import KafkaProducer
from config import CASSANDRA_CONTACT_POINTS, KAFKA_BOOTSTRAP, KAFKA_MONTH_TOPIC

def get_monthly_summary():
    cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS)
    session = cluster.connect("tubs_stats")

    now = datetime.utcnow()
    month_prefix = now.strftime("%Y-%m")
    query = "SELECT camera_id, date, total_count, defective_count FROM tub_counts"
    rows = session.execute(query)

    summary = {}
    for r in rows:
        if not r.date.startswith(month_prefix):
            continue
        cam = r.camera_id
        if cam not in summary:
            summary[cam] = {"total": 0, "defective": 0}
        summary[cam]["total"] += r.total_count
        summary[cam]["defective"] += r.defective_count
    return summary

def emit_to_kafka(summary):
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    now = datetime.utcnow()
    month_str = now.strftime("%Y-%m")
    for cam, data in summary.items():
        total = data["total"]
        defect = data["defective"]
        rate = (defect / total * 100) if total > 0 else 0
        msg = {"camera_id": cam, "month": month_str, "total_count": total, "defective_count": defect, "defect_rate": round(rate, 2)}
        try:
            producer.send(KAFKA_MONTH_TOPIC, key=cam.encode(), value=msg)
        except Exception as e:
            print("kafka send err:", e)
    producer.flush()
    print(f"[{datetime.utcnow()}] Monthly summary emitted for {len(summary)} cameras.")

if __name__ == "__main__":
    s = get_monthly_summary()
    emit_to_kafka(s)
