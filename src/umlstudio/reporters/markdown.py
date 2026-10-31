"""Générateur de rapport exécutif au format Markdown (compatible GitHub / GitLab)."""

from datetime import datetime
from pathlib import Path
from typing import List

from ..core.rules import RuleResult
from ..models.dossier import ConceptionDossier
from .matrix import build_traceability_matrix


def generate_markdown_report(
    dossier: ConceptionDossier,
    rules: List[RuleResult],
    output_path: Path,
) -> None:
    """Génère un rapport de conception complet au format Markdown."""
    matrix = build_traceability_matrix(dossier)

    proj_name = (dossier.cadrage.projet.nom if dossier.cadrage and dossier.cadrage.projet else "") or "Projet umlStudio"
    proj_code = (dossier.cadrage.projet.code if dossier.cadrage and dossier.cadrage.projet else "") or "ARCHI"

    total_rules = len(rules)
    passed_rules = sum(1 for r in rules if r.passed)
    score = round((passed_rules / total_rules) * 100) if total_rules > 0 else 0

    lines: List[str] = [
        f"# Rapport de Conception Logicielle — {proj_name} (`{proj_code}`)",
        "",
        f"> Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')} par **umlStudio**",
        "",
        "## Synthèse Exécutive",
        "",
        f"- **Score de maturité de la conception :** `{score}%` ({passed_rules}/{total_rules} règles validées)",
        f"- **Couverture des exigences par les tests :** `{matrix.coverage_tests_pct}%` ({matrix.tested_exigences}/{matrix.total_exigences})",
        f"- **Couverture des cas d'utilisation par les composants :** `{matrix.coverage_ucs_pct}%` ({matrix.covered_ucs}/{matrix.total_ucs})",
        "",
        "## Audit des 10 Règles Fondamentales & Intégrité",
        "",
        "| Règle | Intitulé | Statut | Diagnostic |",
        "|---|---|:---:|---|",
    ]

    for r in rules:
        status_icon = "✅ PASS" if r.passed else ("⚠️ WARN" if r.severity == "WARNING" else ("ℹ️ INFO" if r.severity == "INFO" else "❌ FAIL"))
        lines.append(f"| `{r.rule_id}` | **{r.title}** | {status_icon} | {r.summary} |")

    # Détail des violations
    all_violations = []
    for r in rules:
        for v in r.violations:
            all_violations.append((r.rule_id, v))

    if all_violations:
        lines.extend([
            "",
            "### Anomalies à Résoudre",
            "",
            "| Règle | Fichier | Élément | Anomalie constatée | Action recommandée |",
            "|---|---|---|---|---|",
        ])
        for rule_id, v in all_violations:
            item = f"`{v.item_id}`" if v.item_id else "-"
            rec = v.recommendation or "-"
            lines.append(f"| `{rule_id}` | `{v.file_name}` | {item} | {v.message} | {rec} |")

    # Matrice de traçabilité
    lines.extend([
        "",
        "## Matrice de Traçabilité de Bout en Bout",
        "",
        "| Obj. | Exigence (EX) | Prio. | Cas d'Usage (UC) | Composants (CMP) | Tests (TST) |",
        "|---|---|:---:|---|---|---|",
    ])

    for row in matrix.rows:
        cmps = ", ".join(f"`{c}`" for c in row.composants_ids) if row.composants_ids else "⚠️ *Non rattaché*"
        tests = ", ".join(f"`{t}`" for t in row.tests_ids) if row.tests_ids else "⚠️ *Non testé*"
        lines.append(
            f"| `{row.objectif_id}` | **{row.exigence_id}** : {row.exigence_titre} | `{row.exigence_priorite}` | `{row.cas_utilisation_id}` {row.cas_utilisation_nom} | {cmps} | {tests} |"
        )

    lines.extend([
        "",
        "---",
        "*Document certifié conforme selon le référentiel de gouvernance logicielle **umlStudio**.*",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
