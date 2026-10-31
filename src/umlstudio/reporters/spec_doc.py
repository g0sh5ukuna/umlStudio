"""Générateur du Document de Spécifications Techniques et Fonctionnelles (Dossier Développeur).

Ce module génère le document unifié complet destiné aux développeurs, architectes et parties prenantes,
permettant de voir le projet 'en gros' (synthèse, vision, périmètre) et 'en détails' (classes, champs requis,
scénarios pas-à-pas, volet sécurité, données personnelles, tests BDD et lots).
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from jinja2 import Environment

from ..models.dossier import ConceptionDossier
from ..core.graph import DependencyGraph


def generate_spec_markdown(dossier: ConceptionDossier, output_path: Path) -> str:
    """Génère le document de conception complet au format Markdown (lisible sur GitHub, GitLab ou éditeur)."""
    p_nom = (dossier.cadrage.projet.nom if dossier.cadrage and dossier.cadrage.projet else "") or "Projet sans nom"
    p_code = (dossier.cadrage.projet.code if dossier.cadrage and dossier.cadrage.projet else "") or "CODE"
    p_comm = (dossier.cadrage.projet.commanditaire.nom if dossier.cadrage and dossier.cadrage.projet and dossier.cadrage.projet.commanditaire else "-")
    p_resp = (dossier.cadrage.projet.responsable_projet.nom if dossier.cadrage and dossier.cadrage.projet and dossier.cadrage.projet.responsable_projet else "-")

    lines: List[str] = [
        f"# Dossier de Spécifications & Conception Logicielle",
        f"## {p_nom} (`{p_code}`)",
        "",
        f"> **Document de référence pour l'équipe de développement et d'architecture.**  ",
        f"> *Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')} par umlStudio.*",
        "",
        "---",
        "",
        "## Table des Matières",
        "1. [Vue d'Ensemble & Cadrage (En gros)](#1-vue-densemble--cadrage-du-projet)",
        "2. [Glossaire & Vocabulaire Métier](#2-glossaire--vocabulaire-métier)",
        "3. [Acteurs & Rôles du Système](#3-acteurs--rôles-du-système)",
        "4. [Exigences & Règles de Gestion](#4-exigences--règles-de-gestion)",
        "5. [Spécifications Détaillées des Cas d'Utilisation](#5-spécifications-détaillées-des-cas-dutilisation)",
        "6. [Architecture Technique & Composants](#6-architecture-technique--composants)",
        "7. [Modèle de Données : Classes & Champs Requis](#7-modèle-de-données--classes--champs-requis)",
        "8. [Volet Sécurité & Protection des Données (RGPD)](#8-volet-sécurité--protection-des-données-rgpd)",
        "9. [Cahier de Recette & Scénarios de Tests (BDD)](#9-cahier-de-recette--scénarios-de-tests-bdd)",
        "10. [Plan de Réalisation & Lots Développeurs](#10-plan-de-réalisation--lots-développeurs)",
        "",
        "---",
        "",
        "## 1. Vue d'Ensemble & Cadrage du Projet",
        "",
        f"- **Commanditaire (Product Owner / Client) :** {p_comm}",
        f"- **Responsable Projet / Lead Architect :** {p_resp}",
        f"- **Statut du document :** `{dossier.cadrage.document.statut if dossier.cadrage else 'brouillon'}` (v{dossier.cadrage.document.version if dossier.cadrage else '0.1.0'})",
        "",
        "### Contexte & Problématique",
    ]

    contexte = (dossier.cadrage.contexte if dossier.cadrage else "") or "Non documenté."
    lines.append(contexte.strip())
    lines.append("")

    # Objectifs
    lines.extend([
        "### Objectifs Mesurables",
        "",
        "| ID | Objectif | Indicateur | Valeur Actuelle | Cible |",
        "|---|---|---|---|---|",
    ])
    if dossier.cadrage and dossier.cadrage.objectifs:
        for obj in dossier.cadrage.objectifs:
            lines.append(f"| `{obj.id}` | {obj.enonce} | {obj.indicateur or '-'} | {obj.valeur_actuelle or '-'} | **{obj.cible or '-'}** |")
    else:
        lines.append("| - | Aucun objectif déclaré | - | - | - |")

    # Périmètre
    lines.extend([
        "",
        "### Délimitation du Périmètre",
        "",
        "#### ✅ Dans le Périmètre (In-Scope)",
    ])
    if dossier.cadrage and dossier.cadrage.perimetre and dossier.cadrage.perimetre.inclus:
        for inc in dossier.cadrage.perimetre.inclus:
            if inc.strip():
                lines.append(f"- {inc.strip()}")
    else:
        lines.append("- *(À préciser)*")

    lines.extend([
        "",
        "#### 🚫 Hors Périmètre (Strictement Exclu / Out-of-Scope)",
    ])
    if dossier.cadrage and dossier.cadrage.perimetre and dossier.cadrage.perimetre.exclu:
        for exc in dossier.cadrage.perimetre.exclu:
            if exc.strip():
                lines.append(f"- **{exc.strip()}**")
    else:
        lines.append("- *(Aucune exclusion déclarée — attention au glissement de périmètre !)*")

    # Contraintes
    if dossier.cadrage and dossier.cadrage.contraintes:
        lines.extend([
            "",
            "### Contraintes Structurantes",
            "",
            "| Type | Énoncé de la contrainte |",
            "|---|---|",
        ])
        for c in dossier.cadrage.contraintes:
            lines.append(f"| `{c.type}` | {c.enonce} |")

    # 2. Glossaire
    lines.extend([
        "",
        "---",
        "",
        "## 2. Glossaire & Vocabulaire Métier",
        "",
        "> **Règle pour les développeurs :** Utilisez rigoureusement les termes canoniques dans le code (noms de tables, classes, variables et DTO). Ne jamais employer les synonymes interdits.",
        "",
        "| Terme Métier | Définition | Synonymes Interdits | Exemple d'Usage |",
        "|---|---|---|---|",
    ])
    if dossier.glossaire and dossier.glossaire.termes:
        for t in dossier.glossaire.termes:
            syns = ", ".join(f"`{s}`" for s in t.synonymes_interdits) if t.synonymes_interdits else "*aucun*"
            lines.append(f"| **{t.terme}** | {t.definition} | ❌ {syns} | *{t.exemple or '-'}* |")
    else:
        lines.append("| - | Glossaire vide | - | - |")

    # 3. Acteurs
    lines.extend([
        "",
        "---",
        "",
        "## 3. Acteurs & Rôles du Système",
        "",
        "| ID | Nom de l'Acteur | Type | Description |",
        "|---|---|---|---|",
    ])
    if dossier.exigences and dossier.exigences.acteurs:
        for act in dossier.exigences.acteurs:
            lines.append(f"| `{act.id}` | **{act.nom}** | `{act.type}` | {act.description or '-'} |")
    else:
        lines.append("| - | Aucun acteur déclaré | - | - |")

    # 4. Exigences
    lines.extend([
        "",
        "---",
        "",
        "## 4. Exigences & Règles de Gestion",
        "",
        "| ID | Type | Énoncé de l'exigence | Mesure Vérifiable / SLA | Priorité |",
        "|---|---|---|---|:---:|",
    ])
    if dossier.exigences and dossier.exigences.exigences:
        for ex in dossier.exigences.exigences:
            lines.append(f"| `{ex.id}` | `{ex.type}` | {ex.enonce} | **{ex.mesure or 'À définir'}** | `{ex.priorite}` |")
    else:
        lines.append("| - | Aucune exigence | - | - | - |")

    # 5. Cas d'utilisation
    lines.extend([
        "",
        "---",
        "",
        "## 5. Spécifications Détaillées des Cas d'Utilisation",
    ])
    if dossier.exigences and dossier.exigences.cas_utilisation:
        for uc in dossier.exigences.cas_utilisation:
            lines.extend([
                "",
                f"### {uc.id} — {uc.nom}",
                "",
                f"- **Acteur Principal :** `{uc.acteur_principal}`" + (f" (Secondaires: {', '.join(uc.acteurs_secondaires)})" if uc.acteurs_secondaires else ""),
                f"- **Exigences Couvertes :** {', '.join(f'`{e}`' for e in uc.exigences) if uc.exigences else 'Aucune'}",
                f"- **Endpoints API :** {', '.join(f'`{ep}`' for ep in uc.endpoints) if uc.endpoints else '*Aucun endpoint direct*'}",
            ])
            if uc.preconditions:
                lines.append(f"- **Préconditions :** {'; '.join(uc.preconditions)}")
            if uc.postconditions:
                lines.append(f"- **Postconditions :** {'; '.join(uc.postconditions)}")

            lines.extend([
                "",
                "**Scénario Nominal :**",
            ])
            for step in uc.scenario_nominal:
                lines.append(f"- {step}")

            if uc.scenarios_alternatifs:
                lines.extend([
                    "",
                    "**Scénarios Alternatifs & Exceptions :**",
                ])
                for alt in uc.scenarios_alternatifs:
                    lines.append(f"- **Condition :** *{alt.condition}*")
                    for s in alt.etapes:
                        lines.append(f"  - {s}")
    else:
        lines.append("\nAucun cas d'utilisation détaillé.\n")

    # 6. Architecture & Composants
    lines.extend([
        "",
        "---",
        "",
        "## 6. Architecture Technique & Composants",
    ])
    if dossier.architecture and dossier.architecture.decisions:
        lines.extend([
            "",
            "### Décisions d'Architecture Majeures (ADR)",
            "",
            "| ID | Sujet | Choix Retenu | Justification & Alternatives Écartées |",
            "|---|---|---|---|",
        ])
        for dec in dossier.architecture.decisions:
            lines.append(
                f"| `{dec.id}` | **{dec.sujet}** | `{dec.choix}` | {dec.pourquoi}"
                + (f"<br>*(Écarté: {dec.alternative_ecartee})*" if dec.alternative_ecartee else "")
                + " |"
            )

    if dossier.architecture and dossier.architecture.composants:
        lines.extend([
            "",
            "### Cartographie des Composants Applicatifs",
            "",
            "| ID | Nom du Composant | Couche | Responsabilité Technique | Techno | Dépendances |",
            "|---|---|---|---|---|---|",
        ])
        for cmp in dossier.architecture.composants:
            deps = ", ".join(f"`{d}`" for d in cmp.depend_de) if cmp.depend_de else "*aucune*"
            lines.append(f"| `{cmp.id}` | **{cmp.nom}** | `{cmp.couche}` | {cmp.responsabilite} | `{cmp.technologie or '-'}` | {deps} |")

    # 7. Modèle de Données (Classes & Champs requis)
    lines.extend([
        "",
        "---",
        "",
        "## 7. Modèle de Données : Classes & Champs Requis",
        "",
        "> **Pour le développeur :** Ce modèle définit les schémas de base de données, les entités ORM et les règles de validation de champs.",
    ])
    if dossier.architecture and dossier.architecture.entites:
        for ent in dossier.architecture.entites:
            lines.extend([
                "",
                f"### Classe / Entité : `{ent.id}` — {ent.nom}",
                "",
                "| Attribut / Champ | Type | Obligatoire (Requis) | Donnée Personnelle (RGPD) |",
                "|---|---|:---:|:---:|",
            ])
            for attr in ent.attributs:
                req_badge = "🔴 **OUI**" if attr.obligatoire else "⚪ Non (optionnel)"
                dp_badge = "🛡️ **OUI (RGPD)**" if attr.donnee_personnelle else "Non"
                lines.append(f"| `{attr.nom}` | `{attr.type or 'String'}` | {req_badge} | {dp_badge} |")

            if ent.relations:
                lines.extend([
                    "",
                    "**Relations associées :**",
                ])
                for rel in ent.relations:
                    lines.append(f"- Relation vers `{rel.vers}` (Cardinalité : `{rel.cardinalite}`)")
    else:
        lines.append("\nAucune entité déclarée.\n")

    # 8. Sécurité & RGPD
    lines.extend([
        "",
        "---",
        "",
        "## 8. Volet Sécurité & Protection des Données (RGPD)",
    ])
    if dossier.architecture and dossier.architecture.securite:
        sec = dossier.architecture.securite
        lines.extend([
            "",
            "### Exigences Techniques de Sécurité",
            "",
            f"- **Authentification :** {sec.authentification or 'À spécifier'}",
            f"- **Autorisation & Rôles (RBAC) :** {sec.autorisation or 'À spécifier'}",
            f"- **Chiffrement en transit :** {sec.chiffrement_transit or 'TLS 1.3 obligatoire'}",
            f"- **Chiffrement au repos :** {sec.chiffrement_repos or 'AES-256'}",
            f"- **Journalisation & Audit :** {sec.journalisation or 'Logs centralisés et non répudiables'}",
        ])

    if dossier.risques and dossier.risques.donnees_personnelles:
        lines.extend([
            "",
            "### Registre des Traitements de Données Personnelles (RGPD / APDP)",
            "",
            "| ID | Entité | Champs Concernés | Finalité Légitime | Base Légale | Conservation | Transfert Hors UE |",
            "|---|---|---|---|---|---|:---:|",
        ])
        for dp in dossier.risques.donnees_personnelles:
            champs_str = ", ".join(f"`{c}`" for c in dp.champs) if dp.champs else "Tous"
            trans_str = "⚠️ OUI" if dp.transfert_hors_pays else "Non"
            lines.append(
                f"| `{dp.id}` | `{dp.entite}` | {champs_str} | {dp.finalite} | `{dp.base_legale}` | {dp.duree_conservation} | {trans_str} |"
            )

    # 9. Tests BDD
    lines.extend([
        "",
        "---",
        "",
        "## 9. Cahier de Recette & Scénarios de Tests (BDD)",
        "",
        "> **Pour le développeur :** Écrivez les tests unitaires et d'intégration avant d'implémenter le code (TDD). Chaque scénario ci-dessous doit passer au vert.",
    ])
    if dossier.tests and dossier.tests.tests:
        for tst in dossier.tests.tests:
            lines.extend([
                "",
                f"### Test `{tst.id}` [{tst.niveau.upper()}]",
                f"- **Exigences Liées :** {', '.join(f'`{e}`' for e in tst.exigences)}",
                f"- **Cas d'Utilisation :** {', '.join(f'`{u}`' for u in tst.cas_utilisation) if tst.cas_utilisation else '-'}",
                f"- **Automatisation requise :** {'Oui' if tst.automatise else 'Non'}",
                "",
                "```gherkin",
                f"Étant donné que : {tst.etant_donne or '(contexte initial)'}",
                f"Quand : {tst.quand or '(action déclenchée)'}",
                f"Alors : {tst.alors or '(résultat attendu vérifiable)'}",
                "```",
            ])
    else:
        lines.append("\nAucun test d'acceptation spécifié.\n")

    # 10. Plan & Lots
    lines.extend([
        "",
        "---",
        "",
        "## 10. Plan de Réalisation & Lots Développeurs",
        "",
        "| Lot | Intitulé | Livrable Attendu | Critère de Fin (Definition of Done) | Dépendances | Estimation |",
        "|---|---|---|---|---|:---:|",
    ])
    if dossier.plan and dossier.plan.lots:
        # Trier par ordre topologique
        try:
            graph = DependencyGraph(dossier.plan.lots)
            sorted_ids = graph.topological_sort()
            lot_map = {l.id: l for l in dossier.plan.lots}
            ordered_lots = [lot_map[lid] for lid in sorted_ids if lid in lot_map]
        except Exception:
            ordered_lots = dossier.plan.lots

        for lot in ordered_lots:
            deps_str = ", ".join(f"`{d}`" for d in lot.depend_de) if lot.depend_de else "*initial*"
            charge_str = f"{lot.charge_estimee.min} - {lot.charge_estimee.max}" if lot.charge_estimee else "-"
            lines.append(
                f"| `{lot.id}` | **{lot.nom}** | {lot.livrable} | **{lot.critere_fin}** | {deps_str} | {charge_str} |"
            )
    else:
        lines.append("| - | Aucun lot défini | - | - | - | - |")

    lines.extend([
        "",
        "---",
        "*Document de conception logicielle certifié conforme et généré automatiquement par umlStudio.*",
    ])

    md_content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")
    return md_content


SPEC_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spécifications Techniques & Fonctionnelles - {{ project_name }} ({{ project_code }})</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4f46e5;
            --primary-dark: #3730a3;
            --primary-bg: #eef2ff;
            --dark: #0f172a;
            --slate-800: #1e293b;
            --slate-700: #334155;
            --slate-600: #475569;
            --slate-400: #94a3b8;
            --slate-200: #e2e8f0;
            --slate-100: #f1f5f9;
            --slate-50: #f8fafc;
            --white: #ffffff;
            --danger: #ef4444;
            --danger-bg: #fef2f2;
            --success: #10b981;
            --success-bg: #ecfdf5;
            --warning: #f59e0b;
            --font: 'Plus Jakarta Sans', system-ui, sans-serif;
            --mono: 'JetBrains Mono', monospace;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: var(--font);
            background: #f8fafc;
            color: var(--dark);
            line-height: 1.6;
        }

        .layout {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar Navigation */
        .sidebar {
            width: 300px;
            background: var(--white);
            border-right: 1px solid var(--slate-200);
            padding: 32px 20px;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            flex-shrink: 0;
        }
        .sidebar-brand {
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--primary);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .sidebar-sub {
            font-size: 0.8rem;
            color: var(--slate-400);
            margin-bottom: 24px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .nav-list { list-style: none; }
        .nav-item { margin-bottom: 6px; }
        .nav-link {
            display: block;
            padding: 8px 12px;
            border-radius: 8px;
            color: var(--slate-600);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        .nav-link:hover {
            background: var(--primary-bg);
            color: var(--primary);
        }

        /* Main Content */
        .content {
            flex: 1;
            padding: 48px 64px;
            max-width: 1100px;
        }

        .hero-banner {
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%);
            color: var(--white);
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
        }
        .hero-banner h1 { font-size: 2.3rem; font-weight: 800; margin-bottom: 8px; }
        .hero-banner .meta-row { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
        .hero-pill {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Section Cards */
        .doc-section {
            background: var(--white);
            border-radius: 16px;
            border: 1px solid var(--slate-200);
            padding: 32px;
            margin-bottom: 32px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
        }
        .doc-section h2 {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--dark);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--slate-100);
        }
        .doc-section h3 {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--slate-800);
            margin: 24px 0 12px 0;
        }

        /* Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.92rem; }
        th {
            background: var(--slate-50);
            padding: 10px 14px;
            text-align: left;
            font-weight: 700;
            color: var(--slate-600);
            border-bottom: 2px solid var(--slate-200);
            font-size: 0.8rem;
            text-transform: uppercase;
        }
        td { padding: 12px 14px; border-bottom: 1px solid var(--slate-200); vertical-align: top; }
        tr:hover td { background: var(--slate-50); }

        /* Code & Badges */
        .code-tag {
            font-family: var(--mono);
            background: var(--slate-100);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.85rem;
            color: var(--slate-800);
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-req { background: #fee2e2; color: #dc2626; }
        .badge-opt { background: #f1f5f9; color: #64748b; }
        .badge-dp { background: #fef3c7; color: #d97706; }
        .badge-prio-must { background: #fee2e2; color: #dc2626; }
        .badge-prio-should { background: #fef3c7; color: #d97706; }
        .badge-prio-could { background: #e0e7ff; color: #4338ca; }

        .callout {
            background: var(--primary-bg);
            border-left: 4px solid var(--primary);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin: 16px 0;
            font-size: 0.9rem;
            color: var(--slate-700);
        }

        .gherkin-block {
            background: #1e293b;
            color: #f8fafc;
            font-family: var(--mono);
            padding: 16px 20px;
            border-radius: 8px;
            margin-top: 8px;
            font-size: 0.88rem;
            line-height: 1.6;
        }
        .gherkin-keyword { color: #f472b6; font-weight: 600; }

        @media (max-width: 900px) {
            .layout { flex-direction: column; }
            .sidebar { width: 100%; height: auto; position: static; }
            .content { padding: 24px; }
        }

        @media print {
            .sidebar { display: none; }
            .content { padding: 0; max-width: 100%; }
            .doc-section { box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="layout">
        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <div class="sidebar-brand">◆ umlStudio</div>
            <div class="sidebar-sub">Dossier de Spécifications</div>
            <ul class="nav-list">
                <li class="nav-item"><a class="nav-link" href="#cadrage">1. Vue Macro & Cadrage</a></li>
                <li class="nav-item"><a class="nav-link" href="#glossaire">2. Glossaire Métier</a></li>
                <li class="nav-item"><a class="nav-link" href="#acteurs">3. Acteurs & Rôles</a></li>
                <li class="nav-item"><a class="nav-link" href="#exigences">4. Exigences & Règles</a></li>
                <li class="nav-item"><a class="nav-link" href="#cas-utilisation">5. Cas d'Utilisation</a></li>
                <li class="nav-item"><a class="nav-link" href="#architecture">6. Architecture & Composants</a></li>
                <li class="nav-item"><a class="nav-link" href="#data-models">7. Classes & Champs Requis</a></li>
                <li class="nav-item"><a class="nav-link" href="#securite">8. Sécurité & RGPD</a></li>
                <li class="nav-item"><a class="nav-link" href="#tests">9. Tests BDD (Recette)</a></li>
                <li class="nav-item"><a class="nav-link" href="#lots">10. Lots & Livrables Développeur</a></li>
            </ul>
        </aside>

        <!-- Main Content -->
        <main class="content">
            <div class="hero-banner">
                <h1>{{ project_name }}</h1>
                <p>{{ context or "Dossier de spécifications techniques et fonctionnelles complet pour les développeurs." }}</p>
                <div class="meta-row">
                    <span class="hero-pill">Code : {{ project_code }}</span>
                    <span class="hero-pill">Commanditaire : {{ commanditaire }}</span>
                    <span class="hero-pill">Lead : {{ responsable }}</span>
                    <span class="hero-pill">Généré le : {{ generated_at }}</span>
                </div>
            </div>

            <!-- 1. Cadrage -->
            <section id="cadrage" class="doc-section">
                <h2>1. Vue Macro & Cadrage du Projet</h2>
                <div class="callout">
                    <strong>Périmètre Exclu (Strictement hors projet) :</strong>
                    {% if cadrage and cadrage.perimetre and cadrage.perimetre.exclu %}
                        {% for exc in cadrage.perimetre.exclu %}
                            {% if exc.strip() %}• {{ exc }} {% endif %}
                        {% endfor %}
                    {% else %}
                        <em>Aucune exclusion déclarée.</em>
                    {% endif %}
                </div>

                <h3>Objectifs Business Cibles</h3>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Objectif</th><th>Indicateur</th><th>Valeur Actuelle</th><th>Cible</th></tr>
                    </thead>
                    <tbody>
                        {% if cadrage and cadrage.objectifs %}
                            {% for obj in cadrage.objectifs %}
                            <tr>
                                <td><span class="code-tag">{{ obj.id }}</span></td>
                                <td><strong>{{ obj.enonce }}</strong></td>
                                <td>{{ obj.indicateur or '-' }}</td>
                                <td>{{ obj.valeur_actuelle or '-' }}</td>
                                <td><strong>{{ obj.cible or '-' }}</strong></td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="5">Aucun objectif déclaré.</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </section>

            <!-- 2. Glossaire -->
            <section id="glossaire" class="doc-section">
                <h2>2. Glossaire & Vocabulaire Métier</h2>
                <p>Ces définitions doivent se retrouver fidèlement dans le code (noms de tables, classes et API).</p>
                <table>
                    <thead>
                        <tr><th>Terme Métier</th><th>Définition</th><th>Synonymes Proscrits</th><th>Exemple</th></tr>
                    </thead>
                    <tbody>
                        {% if glossaire and glossaire.termes %}
                            {% for t in glossaire.termes %}
                            <tr>
                                <td><strong>{{ t.terme }}</strong></td>
                                <td>{{ t.definition }}</td>
                                <td style="color: var(--danger)">{% for s in t.synonymes_interdits %}<span class="code-tag">{{ s }}</span> {% else %}-{% endfor %}</td>
                                <td><em>{{ t.exemple or '-' }}</em></td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="4">Glossaire non renseigné.</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </section>

            <!-- 3. Acteurs -->
            <section id="acteurs" class="doc-section">
                <h2>3. Acteurs & Rôles du Système</h2>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Nom</th><th>Type</th><th>Description</th></tr>
                    </thead>
                    <tbody>
                        {% if exigences and exigences.acteurs %}
                            {% for a in exigences.acteurs %}
                            <tr>
                                <td><span class="code-tag">{{ a.id }}</span></td>
                                <td><strong>{{ a.nom }}</strong></td>
                                <td><span class="badge badge-opt">{{ a.type }}</span></td>
                                <td>{{ a.description }}</td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="4">Aucun acteur défini.</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </section>

            <!-- 4. Exigences -->
            <section id="exigences" class="doc-section">
                <h2>4. Exigences & Règles de Gestion</h2>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Type</th><th>Énoncé</th><th>Mesure Vérifiable / SLA</th><th>Priorité</th></tr>
                    </thead>
                    <tbody>
                        {% if exigences and exigences.exigences %}
                            {% for ex in exigences.exigences %}
                            <tr>
                                <td><span class="code-tag">{{ ex.id }}</span></td>
                                <td><span class="badge badge-opt">{{ ex.type }}</span></td>
                                <td>{{ ex.enonce }}</td>
                                <td><strong>{{ ex.mesure or 'À définir' }}</strong></td>
                                <td><span class="badge badge-prio-{{ ex.priorite | lower }}">{{ ex.priorite }}</span></td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="5">Aucune exigence.</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </section>

            <!-- 5. Cas d'Utilisation -->
            <section id="cas-utilisation" class="doc-section">
                <h2>5. Spécifications des Cas d'Utilisation</h2>
                {% if exigences and exigences.cas_utilisation %}
                    {% for uc in exigences.cas_utilisation %}
                    <div style="border: 1px solid var(--slate-200); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                        <h3><span class="code-tag">{{ uc.id }}</span> {{ uc.nom }}</h3>
                        <p style="margin-bottom: 12px;"><strong>Acteur :</strong> <span class="code-tag">{{ uc.acteur_principal }}</span> | <strong>Exigences :</strong> {% for e in uc.exigences %}<span class="code-tag">{{ e }}</span> {% endfor %}</p>
                        {% if uc.endpoints %}
                        <p style="margin-bottom: 12px;"><strong>Endpoints API associés :</strong> {% for ep in uc.endpoints %}<span class="code-tag">{{ ep }}</span> {% endfor %}</p>
                        {% endif %}
                        <strong>Scénario Nominal :</strong>
                        <ol style="margin-left: 20px; margin-top: 6px;">
                            {% for step in uc.scenario_nominal %}
                            <li>{{ step }}</li>
                            {% endfor %}
                        </ol>
                        {% if uc.scenarios_alternatifs %}
                        <div style="margin-top: 12px;">
                            <strong>Scénarios Alternatifs & Exceptions :</strong>
                            {% for alt in uc.scenarios_alternatifs %}
                            <div style="margin-left: 12px; margin-top: 4px; font-size: 0.9rem;">
                                <em>Condition : {{ alt.condition }}</em>
                                <ul>{% for s in alt.etapes %}<li>{{ s }}</li>{% endfor %}</ul>
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                {% endif %}
            </section>

            <!-- 6. Architecture -->
            <section id="architecture" class="doc-section">
                <h2>6. Architecture & Cartographie des Composants</h2>
                {% if architecture and architecture.decisions %}
                <h3>Décisions Structurantes (ADR)</h3>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Sujet</th><th>Choix</th><th>Motivation & Risque</th></tr>
                    </thead>
                    <tbody>
                        {% for dec in architecture.decisions %}
                        <tr>
                            <td><span class="code-tag">{{ dec.id }}</span></td>
                            <td><strong>{{ dec.sujet }}</strong></td>
                            <td><span class="badge badge-opt">{{ dec.choix }}</span></td>
                            <td>{{ dec.pourquoi }}{% if dec.risque_principal %}<br><small style="color: var(--warning)">Risque : {{ dec.risque_principal }}</small>{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}

                {% if architecture and architecture.composants %}
                <h3>Composants Applicatifs</h3>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Nom</th><th>Couche</th><th>Responsabilité</th><th>Technologie</th></tr>
                    </thead>
                    <tbody>
                        {% for cmp in architecture.composants %}
                        <tr>
                            <td><span class="code-tag">{{ cmp.id }}</span></td>
                            <td><strong>{{ cmp.nom }}</strong></td>
                            <td><span class="badge badge-opt">{{ cmp.couche }}</span></td>
                            <td>{{ cmp.responsabilite }}</td>
                            <td><span class="code-tag">{{ cmp.technologie or '-' }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
            </section>

            <!-- 7. Modèle de Données (Classes & Champs requis) -->
            <section id="data-models" class="doc-section">
                <h2>7. Modèle de Données : Classes & Champs Requis</h2>
                <p>Ce volet est la spécification directe pour la création des modèles ORM et de la base de données.</p>
                {% if architecture and architecture.entites %}
                    {% for ent in architecture.entites %}
                    <div style="margin-bottom: 24px;">
                        <h3>Classe / Entité : <span class="code-tag">{{ ent.id }}</span> {{ ent.nom }}</h3>
                        <table>
                            <thead>
                                <tr><th>Champ / Attribut</th><th>Type</th><th>Caractère Requis</th><th>Protection Données</th></tr>
                            </thead>
                            <tbody>
                                {% for attr in ent.attributs %}
                                <tr>
                                    <td><strong>{{ attr.nom }}</strong></td>
                                    <td><span class="code-tag">{{ attr.type or 'String' }}</span></td>
                                    <td>{% if attr.obligatoire %}<span class="badge badge-req">OBLIGATOIRE</span>{% else %}<span class="badge badge-opt">Optionnel</span>{% endif %}</td>
                                    <td>{% if attr.donnee_personnelle %}<span class="badge badge-dp">RGPD</span>{% else %}-{% endif %}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        {% if ent.relations %}
                        <div style="margin-top: 8px; font-size: 0.9rem;">
                            <strong>Relations :</strong>
                            {% for rel in ent.relations %}
                            Relation vers <span class="code-tag">{{ rel.vers }}</span> (Cardinalité : {{ rel.cardinalite }})
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                {% else %}
                    <p>Aucune entité déclarée.</p>
                {% endif %}
            </section>

            <!-- 8. Sécurité & RGPD -->
            <section id="securite" class="doc-section">
                <h2>8. Volet Sécurité & Données Personnelles (RGPD)</h2>
                {% if architecture and architecture.securite %}
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                    <div style="background: var(--slate-50); padding: 16px; border-radius: 8px;">
                        <strong>Authentification :</strong> {{ architecture.securite.authentification or 'Standard JWT / OIDC' }}<br>
                        <strong>Autorisation (RBAC) :</strong> {{ architecture.securite.autorisation or 'Rôles fins' }}
                    </div>
                    <div style="background: var(--slate-50); padding: 16px; border-radius: 8px;">
                        <strong>Chiffrement Transit :</strong> {{ architecture.securite.chiffrement_transit or 'TLS 1.3' }}<br>
                        <strong>Chiffrement Repos :</strong> {{ architecture.securite.chiffrement_repos or 'AES-256' }}
                    </div>
                </div>
                {% endif %}

                {% if risques and risques.donnees_personnelles %}
                <h3>Registre RGPD des Données Traitées</h3>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Entité</th><th>Finalité Légitime</th><th>Base Légale</th><th>Durée Conservation</th></tr>
                    </thead>
                    <tbody>
                        {% for dp in risques.donnees_personnelles %}
                        <tr>
                            <td><span class="code-tag">{{ dp.id }}</span></td>
                            <td><span class="code-tag">{{ dp.entite }}</span></td>
                            <td>{{ dp.finalite }}</td>
                            <td><span class="badge badge-opt">{{ dp.base_legale }}</span></td>
                            <td>{{ dp.duree_conservation }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
            </section>

            <!-- 9. Tests BDD -->
            <section id="tests" class="doc-section">
                <h2>9. Cahier de Recette & Scénarios BDD (TDD)</h2>
                <p>Critères d'acceptation formulés en syntaxe BDD (Given / When / Then) pour guider le développement piloté par les tests.</p>
                {% if tests and tests.tests %}
                    {% for t in tests.tests %}
                    <div style="margin-bottom: 20px;">
                        <h3>Test <span class="code-tag">{{ t.id }}</span> [{{ t.niveau | upper }}]</h3>
                        <div class="gherkin-block">
                            <span class="gherkin-keyword">Étant donné que</span> {{ t.etant_donne or '(contexte de test)' }}<br>
                            <span class="gherkin-keyword">Quand</span> {{ t.quand or '(action réalisée)' }}<br>
                            <span class="gherkin-keyword">Alors</span> {{ t.alors or '(résultat vérifiable)' }}
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>Aucun test rédigé.</p>
                {% endif %}
            </section>

            <!-- 10. Lots -->
            <section id="lots" class="doc-section">
                <h2>10. Plan de Réalisation & Lots Développeurs</h2>
                <p>Ordre de réalisation respectant scrupuleusement le graphe acyclique de dépendances.</p>
                <table>
                    <thead>
                        <tr><th>Lot</th><th>Intitulé</th><th>Livrable</th><th>Critère de Fin (DoD)</th><th>Dépendances</th></tr>
                    </thead>
                    <tbody>
                        {% if ordered_lots %}
                            {% for lot in ordered_lots %}
                            <tr>
                                <td><span class="code-tag">{{ lot.id }}</span></td>
                                <td><strong>{{ lot.nom }}</strong></td>
                                <td>{{ lot.livrable }}</td>
                                <td><strong>{{ lot.critere_fin }}</strong></td>
                                <td>{% for d in lot.depend_de %}<span class="code-tag">{{ d }}</span> {% else %}<em>initial</em>{% endfor %}</td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="5">Aucun lot défini.</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </section>
        </main>
    </div>
</body>
</html>
"""


def generate_spec_html(dossier: ConceptionDossier, output_path: Path) -> str:
    """Génère le document complet des spécifications techniques au format HTML autonome."""
    p_nom = (dossier.cadrage.projet.nom if dossier.cadrage and dossier.cadrage.projet else "") or "Projet umlStudio"
    p_code = (dossier.cadrage.projet.code if dossier.cadrage and dossier.cadrage.projet else "") or "ARCHI"
    p_comm = (dossier.cadrage.projet.commanditaire.nom if dossier.cadrage and dossier.cadrage.projet and dossier.cadrage.projet.commanditaire else "Commanditaire")
    p_resp = (dossier.cadrage.projet.responsable_projet.nom if dossier.cadrage and dossier.cadrage.projet and dossier.cadrage.projet.responsable_projet else "Tech Lead")

    # Ordre topologique des lots
    ordered_lots = []
    if dossier.plan and dossier.plan.lots:
        try:
            graph = DependencyGraph(dossier.plan.lots)
            sorted_ids = graph.topological_sort()
            lot_map = {l.id: l for l in dossier.plan.lots}
            ordered_lots = [lot_map[lid] for lid in sorted_ids if lid in lot_map]
        except Exception:
            ordered_lots = dossier.plan.lots

    tmpl = Environment(autoescape=True).from_string(SPEC_HTML_TEMPLATE)
    html_content = tmpl.render(
        project_name=p_nom,
        project_code=p_code,
        commanditaire=p_comm,
        responsable=p_resp,
        context=(dossier.cadrage.contexte if dossier.cadrage else ""),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        cadrage=dossier.cadrage,
        glossaire=dossier.glossaire,
        exigences=dossier.exigences,
        architecture=dossier.architecture,
        risques=dossier.risques,
        tests=dossier.tests,
        ordered_lots=ordered_lots,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return html_content
