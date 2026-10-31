# 0003 — Base de données : schéma et migrations dans 03-architecture, effets des appels dans OpenAPI

Date : 2026-10-31 · Statut : acceptée

## Contexte

La spécification listait les entités et leurs champs, sans clés, sans contraintes, sans migrations, et sans dire ce qu'un appel d'API fait réellement en base. Un développeur ne pouvait ni écrire les migrations ni prévoir qu'un INSERT échouera sur une contrainte d'unicité.

## Décision

- Les entités de `03-architecture.yaml` gagnent `table`, et par colonne `cle`, `unique`, `reference`, `sur_suppression`, plus des `contraintes` composées (unique, check, index). Les champs existants ne changent pas : un dossier ancien se charge tel quel.
- Une section `migrations` décrit les changements de schéma dans l'ordre : opérations, réversibilité, reprise de données, statut.
- Dans le contrat OpenAPI, `x-stocke` accepte des objets `{entite, action, champs, detail}` ; `x-lit` déclare les lectures, `x-transaction` le tout-ou-rien. Les contraintes vérifiées et les effets de suppression sont **déduits** du schéma, pas ressaisis par appel.
- La règle 12 vérifie que les clés étrangères et les effets en base visent des entités déclarées.

## Alternatives écartées

- **Lire le schéma depuis la base ou l'ORM** (introspection Django, SQLAlchemy, `pg_dump`) : précis pour un projet existant, mais umlStudio décrit la conception avant le code et ne dépend d'aucune pile.
- **Écrire les contraintes à la main dans chaque appel** : redondant avec le schéma et faux dès qu'une contrainte change.
- **Un fichier `07-donnees.yaml` séparé** : les entités vivent déjà dans l'architecture ; les déplacer casserait les dossiers existants.

## Conséquences

- Un projet existant doit recopier son schéma ; c'est ce qui a été fait pour Mon Répétiteur à partir de `models.py` et de `core/migrations/`.
- Les effets déduits ne voient pas les triggers ni le code applicatif : un `detail` libre permet de les signaler.
