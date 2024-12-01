# Deployment

In order for K8s to access the data generator Docker image, the `image-pull-cr8` secret is needed. This is replicated from the `templates` namespace.

The data generator uses the `admin` user and access the corresponding password from the K8s secret.

```console
$ j2cli -c grafana_config_map.yml k8s_deploy_grafana_demo_data.yml > manifest.yaml
$ kubectl --context k8s.westeurope.azure apply -f manifest.yaml
```
