<div align="center">

# umlStudio

**Concevoir avant de coder, et le prouver.**

Un outil en ligne de commande qui contrôle un dossier de conception logicielle écrit en YAML,
trace chaque exigence jusqu'à son test et produit les documents à remettre à l'équipe.

[![Licence MIT](https://img.shields.io/badge/licence-MIT-1f2937)](LICENSE)
[![Python ≥ 3.10](https://img.shields.io/badge/python-%E2%89%A5%203.10-1f2937)](https://www.python.org/)
[![Statut alpha](https://img.shields.io/badge/statut-alpha%200.1.0-b45309)](#feuille-de-route)

</div>

---

## Pourquoi

Un cahier des charges en traitement de texte vieillit mal : une exigence sans test passe inaperçue, un cas d'utilisation perd son acteur, le périmètre glisse sans que personne ne le voie.

umlStudio remplace ce document par un dossier versionné dans Git, où chaque élément porte un identifiant stable :

```
OBJ-01 → EX-01 → UC-01 → CMP-01 → TST-01
objectif   exigence   cas d'usage   composant   test
```

L'outil vérifie que ces liens existent et que les champs sont renseignés. Il bloque la CI tant que le dossier n'est pas cohérent. Les rapports sont générés à partir de ce même dossier.

## Démarrage

```bash
pip install git+https://github.com/g0sh5ukuna/umlStudio.git

umlstudio init conception --name "Gestion logistique" --code "LOG"
umlstudio check conception
```

Le dossier créé contient un modèle vierge. `check` affiche les champs à remplir, fichier par fichier, avec l'action attendue pour chacun. Une fois le dossier complet, la commande renvoie le code de sortie 0.

## Ce que l'outil contrôle

Dix règles de conception, puis deux contrôles d'intégrité.

| # | Règle | Fichier |
|---|---|---|
| 1 | Toute exigence a un énoncé et une mesure vérifiable | `01-exigences` |
| 2 | Toute exigence est couverte par un test renseigné (action et résultat attendu) | `06-tests` |
| 3 | Tout cas d'utilisation est nommé, décrit pas à pas, et lié à un acteur et à une exigence | `01-exigences` |
| 4 | Tout endpoint OpenAPI est rattaché à un cas d'utilisation | `api/openapi.yaml` |
| 5 | Tout cas d'utilisation est pris en charge par un composant nommé | `03-architecture` |
| 6 | Les termes du glossaire sont définis, et les synonymes interdits n'apparaissent pas dans les exigences | `02-glossaire` |
| 7 | Tout risque ouvert a un responsable et une mitigation | `05-risques` |
| 8 | Toute donnée personnelle a une finalité, une base légale et une durée de conservation (RGPD, APDP) | `05-risques` |
| 9 | Les dépendances entre lots ne forment aucun cycle | `04-plan` |
| 10 | Le périmètre exclu est explicite | `00-cadrage` |
| 11 | Les fichiers validés n'ont pas changé depuis leur validation (empreinte SHA-256) | `validations.yaml` |
| 12 | Aucun identifiant référencé n'est inconnu | tous |

Un champ laissé vide ne compte pas : un test sans résultat attendu ne couvre aucune exigence, et un composant sans nom ne couvre aucun cas d'utilisation.

## Commandes

| Commande | Rôle |
|---|---|
| `umlstudio init <dossier>` | Crée un dossier de conception à partir des modèles |
| `umlstudio check [dossier]` | Lance les 12 contrôles. `--strict` échoue aussi sur les avertissements, `--json` produit une sortie machine |
| `umlstudio matrix [dossier]` | Affiche la matrice de traçabilité objectif → test |
| `umlstudio stats [dossier]` | Affiche les volumes : exigences, cas d'utilisation, risques, tests |
| `umlstudio report [dossier] -f html\|md` | Rapport d'audit : score, anomalies, matrice |
| `umlstudio doc [dossier] -f md\|html` | Spécification destinée aux développeurs : contexte, glossaire, scénarios, modèle de données, sécurité, recette, lots ordonnés |
| `umlstudio sign <fichier> -a <auteur> -e <preuve>` | Enregistre l'empreinte d'un fichier validé dans `validations.yaml` |
| `umlstudio sign-all [dossier] -a <auteur> -e <preuve>` | Fait de même pour les sept fichiers du dossier |

Sans argument, les commandes cherchent le dossier dans le répertoire courant, puis dans `modeles/conception/` et `conception/`.

## Le dossier de conception

```
conception/
├── 00-cadrage.yaml        pourquoi, pour qui, jusqu'où
├── 01-exigences.yaml      acteurs, exigences, cas d'utilisation
├── 02-glossaire.yaml      vocabulaire métier, synonymes interdits
├── 03-architecture.yaml   décisions, composants, entités, déploiement
├── 04-plan.yaml           lots, dépendances, jalons
├── 05-risques.yaml        risques, sécurité, données personnelles
├── 06-tests.yaml          tests d'acceptation (étant donné, quand, alors)
├── validations.yaml       qui a validé quoi, quand, sur quelle version
├── api/openapi.yaml       contrat d'API, écrit avant le code
└── diagrammes/*.puml      diagrammes PlantUML alignés sur les identifiants
```

Les conventions (identifiants jamais réutilisés, provenance de chaque élément, statuts `brouillon` → `soumis` → `valide`) sont décrites dans [modeles/conception/README.md](modeles/conception/README.md).

## Valider un document

Quand la demande de fusion qui modifie un document est approuvée, on enregistre son empreinte :

```bash
umlstudio sign 01-exigences.yaml \
  --author "Alice Martin" --role "Commanditaire" \
  --evidence "https://github.com/org/projet/pull/12"
```

L'auteur et la preuve sont obligatoires, et seuls les fichiers du dossier peuvent être enregistrés. Si le fichier change ensuite, la règle 11 le signale jusqu'à une nouvelle validation.

> **Limite à connaître.** L'empreinte SHA-256 détecte une modification. Elle ne prouve pas l'identité du validateur : n'importe quel contributeur peut relancer `sign`. La garantie d'identité vient de la revue de la demande de fusion référencée en preuve, pas de l'outil.

## Intégration continue

`.github/workflows/conception.yml` :

```yaml
name: Dossier de conception

on:
  pull_request:
    paths: ["conception/**"]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - run: pip install git+https://github.com/g0sh5ukuna/umlStudio.git
      - run: umlstudio check conception --strict
```

## Développement

```bash
git clone https://github.com/g0sh5ukuna/umlStudio.git && cd umlStudio
pip install -e ".[dev]"
pytest --cov=umlstudio
```

La suite couvre les règles, le graphe de dépendances, l'intégrité, les rapports, la CLI et l'installation depuis le wheel.

## Feuille de route

umlStudio est en version 0.1.0. Le format YAML peut encore changer d'ici la 1.0.

- Publication sur PyPI
- Signature vérifiable des validations (Sigstore ou minisign)
- Rendu des diagrammes PlantUML dans les rapports
- Contrôle de cohérence entre les diagrammes et les identifiants du dossier

## Licence

[MIT](LICENSE). Les dossiers de conception produits avec l'outil appartiennent à leurs auteurs.
