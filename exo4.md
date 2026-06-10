# Exercice 4 – Maîtriser la syntaxe Alloy : pipeline, UI et hot reload

## Objectif

L'objectif de cet exercice est de modifier le pipeline Alloy en ajoutant deux processors entre le receiver OTLP et l'exporteur debug. Le premier ajoute l'attribut `deployment.environment=lab` en mode `insert` et le second regroupe les signaux par batch avant leur export.

Le nouveau pipeline est le suivant :

```
OTLP Receiver
      |
      v
Processor Attributes
      |
      v
Processor Batch
      |
      v
Exporter Debug
```

## Modification du fichier config.alloy

J'ai modifié la configuration Alloy afin que les métriques, logs et traces passent par la même chaîne de processors.

```hcl
otelcol.receiver.otlp "default" {
  grpc {
    endpoint = "0.0.0.0:4317"
  }

  http {
    endpoint = "0.0.0.0:4318"
  }

  output {
    metrics = [otelcol.processor.attributes.lab.input]
    logs    = [otelcol.processor.attributes.lab.input]
    traces  = [otelcol.processor.attributes.lab.input]
  }
}

otelcol.processor.attributes "lab" {
  action {
    key = "deployment.environment"
    value = "lab"
    action = "insert"
  }

  output {
    metrics = [otelcol.processor.batch.default.input]
    logs    = [otelcol.processor.batch.default.input]
    traces  = [otelcol.processor.batch.default.input]
  }
}

otelcol.processor.batch "default" {
  output {
    metrics = [otelcol.exporter.debug.default.input]
    logs    = [otelcol.exporter.debug.default.input]
    traces  = [otelcol.exporter.debug.default.input]
  }
}

otelcol.exporter.debug "default" {
  verbosity = "detailed"
}
```

## Rechargement de la configuration

J'ai appliqué la modification sans redémarrer le conteneur grâce au mécanisme de hot reload :

```bash
curl -X POST http://localhost:12345/-/reload
```

## Génération de trafic

J'ai généré du trafic vers l'application Flask afin d'envoyer de nouveaux signaux vers Alloy :

```bash
for i in $(seq 1 20); do curl -s http://localhost:5050/ >/dev/null; done
```

## Vérification

J'ai vérifié dans les logs d'Alloy la présence du nouvel attribut :

```bash
docker compose logs alloy --tail=1000 | grep -i "deployment.environment"
```

J'ai également vérifié dans l'interface Alloy que le nouveau graphe était bien chargé :

```
otelcol.receiver.otlp.default
            |
            v
otelcol.processor.attributes.lab
            |
            v
otelcol.processor.batch.default
            |
            v
otelcol.exporter.debug.default
```

## Résultat obtenu

La configuration Alloy a été modifiée à chaud sans redémarrage du conteneur. Les trois types de signaux OpenTelemetry traversent désormais une chaîne commune de processors avant d'être envoyés vers l'exporteur debug.

L'attribut `deployment.environment=lab` est ajouté aux signaux entrants et le processor batch regroupe les données avant leur export.
