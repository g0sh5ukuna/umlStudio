# umlStudio

Modèles de dossier de conception en YAML et PlantUML, pour cadrer un projet logiciel avant d'écrire le code.

Chaque élément (objectif, exigence, cas d'utilisation, composant, test, risque) a un identifiant stable. Les éléments se lient entre eux par ces identifiants, ce qui permet de vérifier la traçabilité : chaque exigence a un test, chaque cas d'utilisation a un acteur, chaque donnée personnelle a une base légale.

## État

Pour l'instant, seuls les modèles existent. Les dix règles de contrôle décrites dans [modeles/conception/README.md](modeles/conception/README.md) se vérifient encore à la main ; l'outil qui les automatisera reste à écrire.

## Utilisation

1. Copier `modeles/conception/` dans le dépôt de votre projet.
2. Remplir les fichiers dans l'ordre, de `00-cadrage.yaml` à `06-tests.yaml`.
3. Faire valider chaque document par une demande de fusion, puis l'inscrire dans `validations.yaml` avec son hash SHA-256.

Les dossiers remplis appartiennent à votre projet : ils restent dans son dépôt, pas dans celui-ci.

## Contenu

| Fichier | Rôle |
|---|---|
| `00-cadrage.yaml` | Pourquoi, pour qui, jusqu'où |
| `01-exigences.yaml` | Acteurs, exigences, cas d'utilisation |
| `02-glossaire.yaml` | Vocabulaire métier |
| `03-architecture.yaml` | Décisions, composants, données, déploiement |
| `04-plan.yaml` | Lots, dépendances, charges, jalons |
| `05-risques.yaml` | Risques, sécurité, données personnelles |
| `06-tests.yaml` | Tests et critères d'acceptation |
| `validations.yaml` | Registre des validations |
| `diagrammes/` | Diagrammes PlantUML |

## Licence

[MIT](LICENSE)
