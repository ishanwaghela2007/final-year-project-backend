CREATE KEYSPACE IF NOT EXISTS tube_factory
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE tube_factory;

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

CREATE TABLE IF NOT EXISTS batch_status (
    batch_id text PRIMARY KEY,
    produced_count int,
    scratch int,
    crack int,
    bend int,
    hole int,
    target int
);
