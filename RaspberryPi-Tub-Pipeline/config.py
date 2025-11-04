# config.py

# Kafka
KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "tub-status"
KAFKA_MONTH_TOPIC = "tub-monthly-summary"
KAFKA_WEBSOCKET_TOPIC = "farm_tub_updates"

# InfluxDB
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "your-influx-token"
INFLUX_ORG = "org"
INFLUX_BUCKET = "camera_uptime"

# Cassandra
CASSANDRA_CONTACT_POINTS = ["127.0.0.1"]
CASSANDRA_KEYSPACE_EVENTS = "tubs_keyspace"
CASSANDRA_KEYSPACE_STATS = "tubs_stats"

# thresholds and tuning
TEMP_MIN = 2.0
TEMP_MAX = 30.0
FILL_MIN = 20.0
BATCH_SIZE = 50

# API
API_HOST = "0.0.0.0"
API_PORT = 8000

# Misc
LOGGING_LEVEL = "INFO"
