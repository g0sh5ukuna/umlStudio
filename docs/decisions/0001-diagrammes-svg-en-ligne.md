# 0001 — Diagrammes de la spécification : SVG en ligne pour le HTML, Mermaid pour le Markdown

Date : 2026-10-31 · Statut : acceptée

## Contexte

La spécification développeur (`umlstudio doc`) décrivait les cas d'utilisation et l'architecture en listes et en tableaux. Pour voir le système de bout en bout, il fallait reconstituer le dessin de tête. Le HTML est promis « autonome » : un seul fichier, lisible hors connexion et imprimable en PDF.

## Décision

- **HTML** : SVG généré en Python et inséré dans la page. Un diagramme en couloirs par cas d'utilisation (une colonne par acteur, lecture de haut en bas) et une vue de bout en bout (acteurs, composants par couche, systèmes externes).
- **Markdown** : blocs Mermaid (`sequenceDiagram` pour les couloirs, `flowchart LR` pour la vue d'ensemble), rendus nativement par GitHub et GitLab.
- Le couloir d'une étape est l'acteur, ou « le système », cité le plus tôt dans son texte ; une étape sans sujet (« Il valide ») reste dans le couloir précédent. Aucun champ YAML de plus.

## Alternatives écartées

- **Mermaid.js chargé depuis un CDN dans le HTML** : moins de code, mais le fichier cesse d'être autonome (réseau requis, dépendance externe, rendu absent à l'impression si le script ne s'est pas exécuté).
- **PlantUML** : demande Java ou un serveur de rendu.
- **Un champ `couloir` par étape dans le YAML** : exact, mais alourdit la saisie de chaque scénario ; à reconsidérer si l'heuristique se trompe trop souvent.

## Conséquences

- Deux rendus à maintenir pour le même modèle (SVG et Mermaid), qui partagent la même logique d'attribution des couloirs et des liens.
- La mise en page de la vue d'ensemble est en colonnes fixes : un lien qui saute une colonne passe derrière ses boîtes ; il est tracé en pointillé.
