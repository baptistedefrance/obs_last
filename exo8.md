# Exercice 8 – Routage des logs OTLP vers Grafana Loki en mode multi-tenant

## Objectif

Dans le cadre de cet exercice, j’ai mis en place une architecture permettant d’expédier des logs OpenTelemetry provenant de plusieurs applications vers Grafana Loki en utilisant un mécanisme de séparation par tenants. L’objectif était d’isoler les données de chaque équipe en utilisant l’en-tête `X-Scope-OrgID` et de vérifier qu’un tenant ne puisse accéder qu’à ses propres journaux.

L’architecture mise en œuvre repose sur deux applications Flask instrumentées avec OpenTelemetry, Grafana Alloy comme collecteur et routeur de télémétrie, Grafana Loki en mode multi-tenant pour le stockage des logs et Grafana pour leur visualisation.

---

## Configuration de Loki en mode multi-tenant

J’ai commencé par modifier la configuration de Grafana Loki afin d’activer le mode multi-tenant grâce au paramètre :

```yaml
auth_enabled: true
```

Cette configuration impose la présence d’un identifiant d’organisation via l’en-tête HTTP `X-Scope-OrgID` pour toute requête vers l’API Loki.

J’ai également activé la prise en charge des métadonnées structurées nécessaires à l’ingestion de logs au format OTLP avec :

```yaml
limits_config:
  allow_structured_metadata: true
```

La vérification du mode multi-tenant a été réalisée en interrogeant Loki sans fournir de tenant :

```bash
curl -s http://localhost:3100/loki/api/v1/labels
```

L’API doit alors refuser la requête avec une erreur indiquant l’absence d’identifiant d’organisation (`no org id`), confirmant que l’isolation des tenants est active.

---

## Déploiement des applications OpenTelemetry

J’ai déployé deux applications Flask distinctes envoyant leurs logs au format OTLP vers Grafana Alloy.

La première application représente le service de démonstration avec l’attribut de ressource :

```
service.name = demo
```

La seconde application représente un service de paiement avec l’attribut :

```
service.name = payments
```

Pour assurer l’export des logs Python vers OpenTelemetry, j’ai activé l’instrumentation automatique des logs grâce à la variable d’environnement :

```yaml
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true"
```

Les deux applications envoient ensuite leurs logs OTLP vers le récepteur `otelcol.receiver.otlp` d’Alloy.

---

## Routage des logs dans Grafana Alloy

J’ai configuré le composant `otelcol.connector.routing` afin de diriger les logs vers différents exporteurs en fonction de la valeur de l’attribut de ressource `service.name`.

Le langage OTTL a été utilisé pour définir les règles de routage :

* Les logs ayant `service.name = demo` sont envoyés vers le tenant `team-demo`.
* Les logs ayant `service.name = payments` sont envoyés vers le tenant `team-payments`.
* Les logs ne correspondant à aucune règle sont envoyés vers le tenant `default`.

Chaque route utilise un exporteur `otelcol.exporter.otlphttp` pointant vers l’endpoint OTLP natif de Loki :

```
http://loki:3100/otlp
```

L’isolation est réalisée grâce à l’ajout de l’en-tête HTTP :

```
X-Scope-OrgID
```

avec une valeur différente selon le tenant cible.

---

## Configuration de Grafana

Afin de visualiser les données de chaque tenant, j’ai configuré plusieurs datasources Loki dans Grafana :

* `Loki - team-demo`
* `Loki - team-payments`
* `Loki - default`

Chaque datasource ajoute automatiquement son propre en-tête `X-Scope-OrgID`, ce qui permet d’interroger uniquement les logs appartenant au tenant correspondant.

---

## Vérification du routage et de l’isolation

Pour générer des événements, j’ai effectué plusieurs requêtes HTTP vers les deux applications :

```bash
for i in $(seq 1 50); do curl -s http://localhost:5050/ >/dev/null; done

for i in $(seq 1 50); do curl -s http://localhost:5051/ >/dev/null; done
```

J’ai ensuite interrogé directement l’API Loki en spécifiant le tenant souhaité.

Vérification du tenant `team-demo` :

```bash
curl -s -H "X-Scope-OrgID: team-demo" \
http://localhost:3100/loki/api/v1/label/service_name/values | jq
```

Le résultat affiche uniquement le service :

```
demo
```

Vérification du tenant `team-payments` :

```bash
curl -s -H "X-Scope-OrgID: team-payments" \
http://localhost:3100/loki/api/v1/label/service_name/values | jq
```

Le résultat affiche uniquement :

```
payments
```

La même vérification a également été réalisée dans Grafana Explore en sélectionnant les datasources correspondant aux différents tenants. La datasource `Loki - team-demo` ne permet de visualiser que les logs du service `demo`, tandis que la datasource `Loki - team-payments` n’affiche que les logs du service `payments`.

---

## Conclusion

Cet exercice m’a permis de mettre en œuvre une architecture de collecte de logs OTLP multi-tenant avec Grafana Alloy et Grafana Loki. Les logs provenant de plusieurs applications sont correctement routés en fonction de leur attribut `service.name`, puis isolés dans des tenants distincts grâce à l’utilisation de l’en-tête `X-Scope-OrgID`.

La chaîne complète Application OpenTelemetry → Grafana Alloy → routage OTTL → export OTLP HTTP → Grafana Loki multi-tenant → Grafana Explore est pleinement opérationnelle et garantit une séparation logique des données de logs entre les différentes équipes.
