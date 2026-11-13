\timing on
CREATE SCHEMA IF NOT EXISTS scratch_probe;
DROP TABLE IF EXISTS scratch_probe.c75;
CREATE TABLE scratch_probe.c75 AS SELECT * FROM rev1.n_openai_75000;
VACUUM ANALYZE scratch_probe.c75;
SELECT relpages FROM pg_class WHERE oid='scratch_probe.c75'::regclass;
SET maintenance_work_mem='2GB';
SET max_parallel_maintenance_workers=4;
SET client_min_messages=debug1;
\echo serial-default
CREATE INDEX c75_a ON scratch_probe.c75 USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
DROP INDEX scratch_probe.c75_a;
SET min_parallel_table_scan_size=0;
\echo forced-parallel
CREATE INDEX c75_b ON scratch_probe.c75 USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
DROP SCHEMA scratch_probe CASCADE;
