# Exercice 7 – Collecte, traitement et centralisation des logs Docker avec Grafana Alloy et Loki

## Objectif

Dans le cadre de cet exercice, j’ai mis en place une chaîne complète de collecte de logs permettant de récupérer les journaux générés par les conteneurs Docker, de les traiter avec Grafana Alloy puis de les centraliser dans Grafana Loki afin de pouvoir les analyser depuis Grafana Explore.

L’architecture déployée est composée de mon application Flask générant des logs, de Grafana Alloy chargé de la collecte et du traitement des logs, de Grafana Loki assurant le stockage des journaux et de Grafana utilisé pour leur visualisation et leur analyse.

## Déploiement de Loki

J’ai commencé par déployer Grafana Loki en mode mono-binaire avec l’image `grafana/loki:3.3.0`. Conformément aux contraintes de l’exercice, j’ai désactivé l’authentification avec le paramètre `auth_enabled: false` et j’ai configuré un stockage local de type filesystem utilisant le schéma `v13`.

J’ai ensuite vérifié le bon fonctionnement du service Loki grâce à son endpoint de disponibilité :

```bash
curl -s http://localhost:3100/ready
```

La réponse suivante confirme que le service est opérationnel :

```text
ready
```

J’ai également ajouté une datasource Loki dans Grafana afin de pouvoir interroger les journaux directement depuis l’interface Explore.

## Découverte et collecte des logs avec Alloy

Afin de permettre à Grafana Alloy d’accéder aux logs des conteneurs Docker, j’ai monté le socket Docker `/var/run/docker.sock` en lecture seule dans le conteneur Alloy.

J’ai configuré le composant `discovery.docker` pour découvrir automatiquement l’ensemble des conteneurs présents sur l’hôte Docker. J’ai ensuite utilisé `discovery.relabel` afin de récupérer le label Docker Compose `com.docker.compose.service` et de le transformer en un label Loki nommé `service`.

Cette étape me permet d’identifier facilement les logs provenant de chaque service de mon environnement. Dans le cas de mon application Flask, le label récupéré est :

```text
service="app"
```

Les logs découverts sont ensuite collectés grâce au composant `loki.source.docker` puis transmis au pipeline de traitement.

## Traitement et enrichissement des logs

J’ai configuré un composant `loki.process` afin d’appliquer un traitement spécifique uniquement aux logs de mon application Flask. Pour cela, j’ai utilisé un `stage.match` avec le sélecteur LogQL `{service="app"}`, ce qui garantit que les autres conteneurs de l’environnement ne sont pas impactés par ce traitement.

À l’aide d’un `stage.regex`, j’ai extrait les niveaux de sévérité présents dans les messages de logs, notamment `INFO`, `ERROR` et `WARN`. Le niveau extrait est stocké dans un groupe nommé `level`, puis promu en tant que label Loki grâce au composant `stage.labels`.

Cette étape me permet d’effectuer des recherches plus précises dans Grafana, par exemple pour afficher uniquement les erreurs ou uniquement les messages d’information.

Une fois le traitement terminé, les logs sont envoyés vers Grafana Loki grâce au composant `loki.write` utilisant l’endpoint suivant :

```text
http://loki:3100/loki/api/v1/push
```

## Vérification du fonctionnement

Pour générer des événements de test, j’ai envoyé plusieurs requêtes HTTP vers mon application Flask :

```bash
for i in $(seq 1 50); do curl -s http://localhost:5050/ >/dev/null; done
```

Ces requêtes ont permis de produire différents types de logs, par exemple :

```text
INFO successful GET /
ERROR simulated error on GET /
```

J’ai ensuite vérifié les logs du conteneur Alloy afin de m’assurer qu’aucune erreur n’était présente lors de la lecture des logs Docker ou lors de leur envoi vers Loki :

```bash
docker logs alloy
```

L’absence d’erreurs liées au socket Docker ou à l’endpoint de Loki confirme que la chaîne de collecte fonctionne correctement.

## Validation dans Grafana Explore

La validation finale a été réalisée dans Grafana Explore en sélectionnant la datasource Loki.

La requête suivante m’a permis de visualiser l’ensemble des logs provenant de mon application :

```logql
{service="app"}
```

L’affichage des journaux avec ce label confirme que la découverte des conteneurs Docker et la transformation du nom du service Compose en label Loki fonctionnent correctement.

J’ai ensuite utilisé la requête suivante pour afficher uniquement les messages d’information :

```logql
{service="app", level="INFO"}
```

Cette requête retourne les logs de succès générés par l’application.

Enfin, la requête suivante permet d’afficher uniquement les erreurs :

```logql
{service="app", level="ERROR"}
```

Le résultat obtenu confirme que l’extraction du niveau de sévérité par `stage.regex` ainsi que sa promotion en label Loki avec `stage.labels` sont correctement réalisées.

## Conclusion

Grâce à cet exercice, j’ai mis en place une chaîne complète de gestion des logs basée sur Grafana Alloy et Loki. Les logs de mes conteneurs Docker sont automatiquement découverts, enrichis avec des labels pertinents puis centralisés dans Loki.

La chaîne Docker → Grafana Alloy → traitement des logs → Grafana Loki → Grafana Explore est entièrement opérationnelle et me permet d’effectuer des recherches précises selon le service concerné et le niveau de sévérité des messages.
