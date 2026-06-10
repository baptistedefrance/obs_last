# Exercice 6 – Pipeline de métriques OpenTelemetry vers Grafana Mimir avec Alloy

## Contexte

Dans le cadre de cet exercice, j’ai mis en place une chaîne de traitement permettant de collecter les métriques OpenTelemetry d’une application Flask, de les traiter dans Grafana Alloy puis de les stocker dans Grafana Mimir au format Prometheus.

L’architecture mise en œuvre repose sur plusieurs composants conteneurisés avec Docker Compose : l’application Flask instrumentée avec OpenTelemetry, Grafana Alloy en tant que collecteur de télémétrie, Grafana Mimir comme base de stockage des métriques et Grafana pour leur visualisation.

## Configuration du pipeline Alloy

J’ai configuré un récepteur `otelcol.receiver.otlp` dans Alloy afin de recevoir les données OTLP envoyées par l’application sur les protocoles HTTP et gRPC.

Les logs et les traces ont été conservés vers un exporteur `debug`, conformément aux contraintes de l’exercice. Les métriques ont quant à elles été envoyées vers un processeur `otelcol.processor.attributes` afin d’ajouter des informations de contexte sans écraser d’éventuels attributs existants.

Les attributs suivants ont été ajoutés :

* `team = platform`
* `deployment.environment = lab`

Après cette étape d’enrichissement, les métriques ont été converties du format OpenTelemetry vers le modèle Prometheus grâce au composant `otelcol.exporter.prometheus`, puis envoyées vers Grafana Mimir via un `prometheus.remote_write`.

## Validation du fonctionnement

Pour valider le bon fonctionnement de la chaîne de traitement, j’ai généré plusieurs requêtes HTTP vers l’application Flask afin de produire des métriques applicatives.

Les requêtes réalisées directement sur l’API Prometheus de Mimir ont confirmé la présence des métriques HTTP, notamment `http_server_duration_milliseconds_count`. Les séries récupérées contiennent bien les labels `team="platform"` et `deployment_environment="lab"`, confirmant que l’enrichissement des données a été réalisé avant leur conversion vers Prometheus.

L’ensemble du pipeline OpenTelemetry → Grafana Alloy → conversion Prometheus → Grafana Mimir est donc opérationnel et permet de centraliser les métriques applicatives enrichies.
