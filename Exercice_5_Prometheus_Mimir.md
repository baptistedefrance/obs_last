# Exercice 5 – Scraper Prometheus et envoyer vers Mimir

## Objectif

Dans cet exercice, j’ai déployé Mimir comme backend de métriques, node_exporter comme cible Prometheus et Grafana pour visualiser les données. J’ai ensuite configuré Alloy pour scraper node_exporter toutes les 15 secondes et envoyer les métriques vers Mimir avec `remote_write`.

## Fichiers ajoutés

J’ai créé les dossiers suivants :

```bash
mkdir -p mimir grafana/provisioning/datasources
```

## Configuration Mimir

Fichier `mimir/config.yml` :

```yaml
target: all

multitenancy_enabled: false

server:
  http_listen_port: 9009

common:
  storage:
    backend: filesystem
    filesystem:
      dir: /data/mimir

blocks_storage:
  backend: filesystem
  filesystem:
    dir: /data/mimir/blocks
  tsdb:
    dir: /data/mimir/tsdb

compactor:
  data_dir: /data/mimir/compactor

ruler_storage:
  backend: filesystem
  filesystem:
    dir: /data/mimir/ruler

alertmanager_storage:
  backend: filesystem
  filesystem:
    dir: /data/mimir/alertmanager
```

## Datasource Grafana

Fichier `grafana/provisioning/datasources/datasources.yml` :

```yaml
apiVersion: 1

datasources:
  - name: Mimir
    type: prometheus
    access: proxy
    url: http://mimir:9009/prometheus
    isDefault: true
```

## Docker Compose

J’ai ajouté les services `mimir`, `node_exporter` et `grafana` dans `docker-compose.yml` :

```yaml
  mimir:
    image: grafana/mimir:2.14.0
    container_name: mimir
    command:
      - -config.file=/etc/mimir/config.yml
    ports:
      - "9009:9009"
    volumes:
      - ./mimir/config.yml:/etc/mimir/config.yml
      - mimir-data:/data/mimir

  node_exporter:
    image: prom/node-exporter:v1.8.2
    container_name: node_exporter
    ports:
      - "9100:9100"

  grafana:
    image: grafana/grafana:11.4.0
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - mimir
```

J’ai aussi ajouté le volume en bas du fichier :

```yaml
volumes:
  mimir-data:
```

## Configuration Alloy

J’ai ajouté ces composants dans `config.alloy` :

```hcl
prometheus.scrape "node_exporter" {
  targets = [
    {
      __address__ = "node_exporter:9100",
    },
  ]

  scrape_interval = "15s"

  forward_to = [
    prometheus.remote_write.mimir.receiver,
  ]
}

prometheus.remote_write "mimir" {
  endpoint {
    url = "http://mimir:9009/api/v1/push"
  }
}
```

## Déploiement

J’ai démarré la stack :

```bash
docker compose up -d
```

J’ai rechargé Alloy :

```bash
curl -X POST http://localhost:12345/-/reload
```

## Vérification

J’ai vérifié que Mimir répondait avec la requête `up` :

```bash
curl -s "http://localhost:9009/prometheus/api/v1/query?query=up" | jq
```

J’ai ensuite ouvert Grafana :

```text
http://localhost:3000
```

Dans `Explore`, j’ai sélectionné la datasource `Mimir`, puis lancé la requête :

```promql
up
```

## Résultat obtenu

La requête `up` retourne bien une cible Prometheus. Alloy scrape `node_exporter` toutes les 15 secondes et envoie les métriques vers Mimir avec `remote_write`. Grafana permet ensuite de visualiser les métriques stockées dans Mimir.
