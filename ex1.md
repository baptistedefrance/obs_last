# Exercice 1 – Mettre Alloy en route

## Objectif

Dans cet exercice, j’ai mis en place un conteneur Grafana Alloy avec une configuration minimale. L’objectif était de recevoir des données OTLP en HTTP et en gRPC, puis de les envoyer vers un exporteur debug afin de vérifier le fonctionnement du pipeline depuis l’interface web d’Alloy.

## Fichiers créés

J’ai créé un dossier de travail nommé `alloy-tp`.

```bash
mkdir alloy-tp
cd alloy-tp
```

Dans ce dossier, j’ai créé deux fichiers :

```bash
touch docker-compose.yml
touch config.alloy
```

## Configuration Alloy

Dans le fichier `config.alloy`, j’ai déclaré un receiver OTLP capable de recevoir les signaux en gRPC sur le port `4317` et en HTTP sur le port `4318`.

J’ai ensuite ajouté un exporteur debug avec le niveau de détail `detailed`, afin d’afficher précisément les traces, métriques et logs reçus.

```hcl
otelcol.receiver.otlp "default" {
  grpc {
    endpoint = "0.0.0.0:4317"
  }

  http {
    endpoint = "0.0.0.0:4318"
  }

  output {
    traces  = [otelcol.exporter.debug.default.input]
    metrics = [otelcol.exporter.debug.default.input]
    logs    = [otelcol.exporter.debug.default.input]
  }
}

otelcol.exporter.debug "default" {
  verbosity = "detailed"
}
```

## Configuration Docker Compose

Dans le fichier `docker-compose.yml`, j’ai utilisé l’image officielle `grafana/alloy:v1.5.1`.

J’ai exposé les ports nécessaires pour OTLP et pour l’interface web d’Alloy. J’ai également monté le fichier `config.alloy` dans le conteneur afin que la configuration soit chargée depuis un fichier.

```yaml
services:
  alloy:
    image: grafana/alloy:v1.5.1
    container_name: alloy
    restart: unless-stopped
    ports:
      - "4317:4317"
      - "4318:4318"
      - "12345:12345"
    volumes:
      - ./config.alloy:/etc/alloy/config.alloy
    command:
      - run
      - /etc/alloy/config.alloy
      - --server.http.listen-addr=0.0.0.0:12345
```

## Lancement du conteneur

J’ai lancé la stack avec Docker Compose.

```bash
docker compose up -d
```

J’ai ensuite vérifié que le conteneur Alloy était bien démarré.

```bash
docker ps
```

## Vérification de l’état d’Alloy

Pour vérifier que le service Alloy était prêt, j’ai exécuté la commande suivante :

```bash
curl -s http://localhost:12345/-/ready
```

Le résultat attendu était :

```text
Alloy is ready
```

## Vérification dans l’interface web

J’ai ensuite ouvert l’interface web d’Alloy depuis mon navigateur :

```text
http://localhost:12345
```

Dans l’onglet `Graph`, j’ai vérifié la présence des deux composants suivants :

```text
otelcol.receiver.otlp.default
otelcol.exporter.debug.default
```

J’ai également vérifié que le receiver OTLP était bien relié à l’exporteur debug pour les trois signaux :

```text
traces
metrics
logs
```

## Commandes utiles

Pour consulter les logs du conteneur Alloy :

```bash
docker logs -f alloy
```

Pour arrêter la stack :

```bash
docker compose down
```

Pour redémarrer la stack après modification de la configuration :

```bash
docker compose down
docker compose up -d
```

## Résultat

À la fin de l’exercice, j’ai obtenu un conteneur Grafana Alloy fonctionnel. Il écoute correctement les ports OTLP `4317` et `4318`, expose son interface web sur le port `12345`, et transmet les trois signaux observabilité vers un exporteur debug.

La commande de vérification retourne bien :

```text
Alloy is ready
```

L’interface web permet également de visualiser le pipeline dans l’onglet `Graph`.
