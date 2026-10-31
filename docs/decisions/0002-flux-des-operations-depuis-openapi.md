# 0002 — Flux des opérations : OpenAPI comme source, extension x-stocke pour le stockage

Date : 2026-10-31 · Statut : acceptée

## Contexte

La vue de bout en bout montrait quels composants servent quels acteurs, pas ce qui circule. Il fallait voir, appel par appel : l'endpoint, la méthode, la sécurité, les champs attendus, ce qui est enregistré, ce qui se passe en cas d'échec, puis l'appel suivant.

## Décision

- Les appels sont lus dans `api/openapi.yaml`, déjà prévu par le dossier comme « contrat d'API écrit avant le code ». Méthode, chemin, sécurité (`securitySchemes`, héritage global, `security: []` = public), champs requis (paramètres et corps, `$ref` et `allOf` résolus), réponses 1xx-3xx en succès et 4xx-5xx en échec.
- Le stockage, qu'OpenAPI ne décrit pas, est déclaré par l'extension `x-stocke: [ENT-xx]`. Absente = « non déclaré » ; liste vide = « rien n'est stocké ».
- L'enchaînement suit l'ordre de `endpoints` dans chaque cas d'utilisation ; la fin du flux reprend ses postconditions.

## Alternatives écartées

- **Décrire les appels dans 03-architecture.yaml** : deuxième source de vérité à côté du contrat OpenAPI, qui divergerait.
- **Déduire le stockage du code** : hors de portée d'un outil qui lit un dossier de conception, et faux dès que le code change.
- **Un champ `suite` par opération** : l'ordre des endpoints du cas d'utilisation suffit tant qu'il n'y a pas de branche conditionnelle entre appels réussis.

## Conséquences

- Un contrat OpenAPI généré automatiquement (drf-spectacular, FastAPI) donne déjà méthode, champs et réponses ; seul `x-stocke` est à ajouter à la main.
- Le flux est linéaire : une branche « si succès, selon le cas » n'est pas représentée.
