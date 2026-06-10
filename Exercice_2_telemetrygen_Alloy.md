# Exercice 2 – Envoyer des données OTLP avec telemetrygen

## Objectif de l’exercice

Dans cet exercice, j’ai utilisé l’outil `telemetrygen` pour générer de fausses données OpenTelemetry et les envoyer vers Grafana Alloy.

L’objectif était de vérifier que le pipeline configuré dans l’exercice précédent fonctionne réellement en réceptionnant les trois types de signaux :

- traces ;
- métriques ;
- logs.

Les données sont envoyées en OTLP/gRPC vers Alloy sur le port `4317`.

## Principe de fonctionnement

Dans l’exercice précédent, j’ai configuré Alloy avec un receiver OTLP et un exporteur debug.

Le fonctionnement est donc le suivant :

```text
telemetrygen
     |
     | OTLP/gRPC
     | port 4317
     v
Grafana Alloy
     |
     v
otelcol.exporter.debug
     |
     v
logs du conteneur Alloy
```

L’outil `telemetrygen` joue le rôle d’une application qui produit des données d’observabilité. Ces données sont envoyées vers Alloy, puis affichées dans les logs grâce à l’exporteur debug.

## Prérequis

Avant de commencer cet exercice, j’ai conservé la stack Alloy de l’exercice 1 en fonctionnement.

Je vérifie que le conteneur Alloy est bien actif :

```bash
docker ps
```

Je dois voir un conteneur nommé :

```text
alloy
```

Je vérifie également qu’Alloy est prêt :

```bash
curl -s http://localhost:12345/-/ready
```

Le résultat attendu est :

```text
Alloy is ready
```

## Identification du réseau Docker

Pour que `telemetrygen` puisse joindre Alloy avec le nom DNS `alloy:4317`, le conteneur telemetrygen doit être lancé sur le même réseau Docker que le conteneur Alloy.

Je liste les réseaux Docker disponibles :

```bash
docker network ls
```

Avec Docker Compose, le réseau porte généralement un nom basé sur le dossier du projet, par exemple :

```text
obs_default
```

Pour trouver précisément le réseau utilisé par Alloy, j’exécute :

```bash
docker inspect alloy --format '{{range $k, $v := .NetworkSettings.Networks}}{{println $k}}{{end}}'
```

Je note le nom du réseau retourné. Dans mon cas :

```text
obs_default
```

Dans les commandes suivantes, je remplace donc `<NOM_DU_RESEAU>` par le réseau réellement utilisé par Alloy.

## Envoi de traces avec telemetrygen

J’envoie au minimum 5 traces vers Alloy avec la commande suivante :

obs_default :

```bash
docker run --rm --network obs_default ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest traces --otlp-endpoint alloy:4317 --otlp-insecure --traces 5
```

Cette commande génère 5 traces et les envoie à Alloy via OTLP/gRPC.

## Vérification de la réception des traces

Je vérifie les logs Alloy :

```bash
docker compose logs alloy | grep -E "ResourceSpans" | head
```

Je peux aussi afficher les logs en direct :

```bash
docker compose logs -f alloy
```

Je dois voir apparaître des blocs contenant :

```text
ResourceSpans
```

Cela confirme que les traces ont bien été reçues par Alloy.

## Envoi de métriques avec telemetrygen

J’envoie des métriques pendant 10 secondes :

```bash
docker run --rm --network obs_default ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest metrics --otlp-endpoint alloy:4317 --otlp-insecure --duration 10s
```

Cette commande génère des séries de métriques artificielles pendant 10 secondes et les transmet à Alloy.

## Vérification de la réception des métriques

Je vérifie les logs Alloy :

```bash
docker compose logs alloy | grep -E "ResourceMetrics" | head
```

Je dois voir apparaître :

```text
ResourceMetrics
```

Cela confirme qu’Alloy reçoit bien les métriques envoyées par telemetrygen.

## Envoi de logs avec telemetrygen

J’envoie des logs pendant 5 secondes :

```bash
docker run --rm --network obs_default ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest logs --otlp-endpoint alloy:4317 --otlp-insecure --duration 5s
```

Cette commande génère des logs OpenTelemetry et les envoie à Alloy.

## Vérification de la réception des logs

Je vérifie les logs Alloy :

```bash
docker compose logs alloy | grep -E "ResourceLogs" | head
```

Je dois voir apparaître :

```text
ResourceLogs
```

Cela confirme qu’Alloy reçoit bien les logs envoyés par telemetrygen.

## Vérification globale

Pour vérifier les trois signaux en une seule commande, j’exécute :

```bash
docker compose logs alloy | grep -E "ResourceSpans|ResourceMetrics|ResourceLogs" | head
```

Le résultat doit contenir au moins un des éléments suivants :

```text
ResourceSpans
ResourceMetrics
ResourceLogs
```

Pour suivre les données reçues en temps réel :

```bash
docker compose logs -f alloy
```

## Résultat obtenu

À la fin de l’exercice, j’ai réussi à envoyer les trois types de signaux OpenTelemetry vers Grafana Alloy avec `telemetrygen`.

J’ai envoyé :

- 5 traces ;
- 10 secondes de métriques ;
- 5 secondes de logs.

Les logs du conteneur Alloy ont confirmé la bonne réception des données grâce à la présence des blocs `ResourceSpans`, `ResourceMetrics` et `ResourceLogs`.

Cet exercice m’a permis de valider concrètement que le receiver OTLP configuré dans Alloy fonctionne correctement en gRPC sur le port `4317`.
