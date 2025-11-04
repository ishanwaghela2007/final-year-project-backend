# process/kafka_producer.py
import json
from kafka import KafkaProducer
from config import KAFKA_BOOTSTRAP

def create_producer():
    p = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=100,
        max_request_size=1048576
    )
    return p

def send_event(producer, topic, key, value):
    try:
        producer.send(topic, key=key.encode('utf-8') if key else None, value=value)
    except Exception as e:
        print("kafka send error:", e)
