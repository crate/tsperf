CREATE TABLE "doc"."timeseries" (
    "ts" TIMESTAMP WITH TIME ZONE,
    "g_ts_week" TIMESTAMP WITH TIME ZONE GENERATED ALWAYS AS date_trunc('week', "ts"),
    "payload" OBJECT(DYNAMIC) AS (
      "button_press" INT,
      "line" INT,
      "plant" INT,
      "sensor_id" INT,
      "value" REAL
   )
)
CLUSTERED INTO 21 SHARDS
PARTITIONED BY ("g_ts_week")
WITH (
    number_of_replicas = 1
)

--timescale create table statement
CREATE TABLE timeseries(
    ts TIMESTAMP NOT NULL,
    ts_week TIMESTAMP NOT NULL,
    payload jsonb NOT NULL
);

SELECT create_hypertable('timeseries', 'ts', 'ts_week', 10);