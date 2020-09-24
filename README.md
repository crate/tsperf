# Timeseries data generator

The datagenerator has it is own in-depth [documentation](DATA_GENERATOR.md).
For the purpose of capacity testing it simulates the generation of timeseries
data, without the need to setup a ingest chain (which in our case would be a
Azure IoTHub, RabbitMQ, eg.)

## How to achieve maximum ingest performance?
The datagenerator implements batch inserts where possible. A back-pressure
mechanism is built-in, to adjust for the best possible batch size by
setting the batch size dynamically.

A single instance of the datagenerator might do up to 20-40k events per second
for cratedb (depending on the cluster size). To find the maximum ingest
possible, **multiple instances** are required.

For this purpose we created kubernetes jobs, which allows an easy scale and
distribution of multiple nodes.

While some of the target databases reach their maximum ingest by running 6-8
datagenerators in parallel, others might required much more concurrency until
they max out.

## kubernetes to the rescue
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  labels:
    k8s-app: datagenerator
  name: dg-{{ ID_START }}
  namespace: "{{ kubernetes.namespace }}"
  labels:
    app.kubernetes.io/name: {{ kubernetes.name }}
spec:
  backoffLimit: 0
  template:
    metadata:
      annotations:
        prometheus.io/port: "8000"
        prometheus.io/scrape: "true"
        prometheus.io/path: "/metrics"
      labels:
        k8s-app: datagenerator
        app.kubernetes.io/name: {{ kubernetes.name }}
    spec:
      imagePullSecrets:
      - name: image-pull-cr8
      containers:
      - name: datagenerator
        image: registry.cr8.net/data-generator:{{ version }}
        ports:
        - containerPort: 8000
          protocol: TCP
        resources:
          requests:
            cpu: "500m"
            memory: "8196Mi"
          limits:
            cpu: "4000m"
            memory: "8196Mi"
        volumeMounts:
        - name: datamodel
          mountPath: "/temperature.json"
          subPath: temperature.json
        env:
        - name: ID_START
          value: "{{ ID_START }}"
        - name: ID_END
          value: "{{ ID_END }}"
        - name: HOST
          value: {{ db.crateuri }}
        - name: INGEST_MODE
          value: "1"
        - name: INGEST_SIZE
          value: "2400000"
        - name: MODEL_PATH
          value: "/temperature.json"
        - name: INGEST_DELTA
          value: "0.5"
        - name: INGEST_TS
          value: "1600163743.500"
        - name: TABLE_NAME
          value: "doc.timeseries2"
        - name: SHARDS
          value: "28"
        - name: USERNAME
          valueFrom:
            secretKeyRef:
              name: datagenerator
              key: crate_user
        - name: PASSWORD
          valueFrom:
            secretKeyRef:
              name: datagenerator
              key: crate_password
      restartPolicy: Never
      volumes:
      - name: datamodel
        configMap:
          name: datamodel

```
*) secrets, configmap **NOT** shown here.

s
