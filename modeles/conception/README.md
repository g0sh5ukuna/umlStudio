# Dossier de conception

Ce dossier est la source de vérité du projet. **Aucun code de production avant que tous les documents soient au statut `valide`.**
Les prototypes techniques sont autorisés : branche `spike/*`, limités dans le temps, jetés après usage.

## Fichiers

| Fichier | Répond à | Validé par |
|---|---|---|
| `00-cadrage.yaml` | Pourquoi, pour qui, jusqu'où | Commanditaire |
| `01-exigences.yaml` | Acteurs, exigences, cas d'utilisation | Commanditaire / métier |
| `02-glossaire.yaml` | Vocabulaire métier | Métier |
| `03-architecture.yaml` | Composants, données, interfaces, déploiement | Autorité technique |
| `api/openapi.yaml` | Contrat d'API (écrit avant le code) | Autorité technique |
| `04-plan.yaml` | Lots, dépendances, charges, jalons | Responsable projet |
| `05-risques.yaml` | Risques, sécurité, données personnelles | Responsable projet + sécurité |
| `06-tests.yaml` | Tests et critères d'acceptation | Commanditaire + technique |
| `validations.yaml` | Qui a validé quoi, quand, sur quelle version | — |
| `diagrammes/*.puml` | Diagrammes PlantUML (rendu local) | Avec le document lié |

## Conventions

- **Identifiants stables**, jamais réutilisés : `OBJ-01`, `ACT-01`, `EX-01`, `UC-01`, `CMP-01`, `ENT-01`, `LOT-01`, `RSK-01`, `DP-01`, `TST-01`. Un élément supprimé passe en `statut: abandonne`, il n'est pas effacé.
- **Les liens se font par identifiant.** Les endpoints sont référencés par leur `operationId` OpenAPI.
- **Provenance obligatoire** sur chaque élément : `source: humain | document | deduit`. Un élément `deduit` doit être confirmé par un humain avant validation.
- **Ce qui manque s'écrit** dans `non_trouve` (cadrage). Un trou déclaré vaut mieux qu'un trou comblé par supposition.
- **Statuts de document** : `brouillon` → `soumis` → `valide`. Toute modification d'un fichier validé le repasse à `soumis`.
- **Validation** = demande de fusion approuvée sur la forge + entrée dans `validations.yaml` (hash SHA-256 du fichier).

## Règles de contrôle (appliquées à la main aujourd'hui, par l'outil demain)

1. Toute exigence a une `mesure` vérifiable.
2. Toute exigence est liée à au moins un test.
3. Tout cas d'utilisation est lié à au moins une exigence et un acteur.
4. Tout endpoint OpenAPI est lié à au moins un cas d'utilisation.
5. Tout cas d'utilisation est couvert par au moins un composant.
6. Tout terme métier utilisé dans les exigences est défini dans le glossaire.
7. Tout risque a un responsable et une mitigation.
8. Toute donnée personnelle a une finalité, une base légale et une durée de conservation.
9. Le graphe des dépendances du plan ne contient pas de cycle.
10. Le périmètre exclu n'est pas vide.

## Séparation

Ces modèles viennent d'un outil open source personnel. **Les dossiers remplis appartiennent au projet et à son propriétaire** : ils restent dans le dépôt du projet, jamais dans le dépôt de l'outil.
