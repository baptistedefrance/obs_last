# Exercice 3 – Instrumenter une application Flask avec OpenTelemetry

## Objectif

L'objectif de cet exercice est de déployer une application Flask instrumentée automatiquement avec OpenTelemetry afin d'envoyer des traces, métriques et logs vers Grafana Alloy en OTLP HTTP.

## Mise en place de l'application

J'ai créé une application Flask exposant un endpoint `/` qui retourne aléatoirement un code HTTP `200` ou `500` avec un délai inférieur à 500 ms.

### app.py

```python
from flask import Flask
import random
import time
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route("/")
def index():
    time.sleep(random.uniform(0.05, 0.5))

    if random.random() < 0.1:
        logging.error("simulated error on GET /")
        return "simulated error", 500

    logging.info("successful GET /")
    return "ok", 200

app.run(host="0.0.0.0", port=5050)
```

### requirements.txt

```txt
flask
opentelemetry-distro
opentelemetry-exporter-otlp
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && opentelemetry-bootstrap -a install

COPY app.py .

CMD ["opentelemetry-instrument", "python", "/app.py"]
```

## Intégration dans docker-compose

J'ai ajouté un nouveau service `demo` à ma stack Docker avec les variables d'environnement OpenTelemetry :

```yaml
demo:
  build: ./app
  container_name: demo-flask
  ports:
    - "5050:5050"

  environment:
    OTEL_SERVICE_NAME: demo
    OTEL_EXPORTER_OTLP_ENDPOINT: http://alloy:4318
    OTEL_EXPORTER_OTLP_PROTOCOL: http/protobuf
    OTEL_TRACES_EXPORTER: otlp
    OTEL_METRICS_EXPORTER: otlp
    OTEL_LOGS_EXPORTER: otlp
```

## Déploiement et tests

Construction et démarrage :

```bash
docker compose up -d --build
```

Génération de trafic :

```bash
for i in $(seq 1 30); do curl -s http://localhost:5050/ >/dev/null; done
```

Vérification des données reçues par Alloy :

```bash
docker compose logs alloy --tail=300 | grep -E "service.name|GET /|simulated|http.server.duration"
```

## Résultat obtenu

L'application Flask a été instrumentée sans modifier le code avec OpenTelemetry. Les traces, métriques et logs sont transmis à Alloy via OTLP HTTP sur le port `4318`.

Les logs d'Alloy montrent la présence du service `demo`, des requêtes HTTP `GET /`, des erreurs simulées et des métriques de durée `http.server.duration`.
