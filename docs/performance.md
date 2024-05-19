# Ingest Performance

## Introduction

The data generator uses batch inserts where possible. A back-pressure
mechanism is built-in, to adjust for the best possible batch size by
reconfiguring it dynamically.

A single instance of the data generator might do up to 20-40k events per second
for CrateDB, depending on the cluster size. To find the maximum possible ingest
rate, **multiple instances** are required.

## Kubernetes

For the purpose of parallelizing the ingest, Kubernetes jobs allow to easily
deploy multiple instances of the data generator.

While some target databases reach their maximum ingest by running 6-8
data generator instances in parallel, others might require a higher
concurrency until they max out.

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
        image: ghcr.io/crate/tsperf:latest
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
        env:
        - name: ID_START
          value: "{{ ID_START }}"
        - name: ID_END
          value: "{{ ID_END }}"
        - name: ADDRESS
          value: {{ db.crateuri }}
        - name: INGEST_MODE
          value: "1"
        - name: INGEST_SIZE
          value: "2400000"
        - name: SCHEMA
          value: "tsperf.schema.basic:environment.json"
        - name: TIMESTAMP_DELTA
          value: "0.5"
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
```
Remark: Secrets and configmap are **NOT** shown here.
