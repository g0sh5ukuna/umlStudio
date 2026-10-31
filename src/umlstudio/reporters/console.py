"""Affichage console stylisé avec Rich pour les résultats d'audit et les statistiques."""

from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ..core.rules import RuleResult
from .matrix import TraceabilityReport
from ..models.dossier import ConceptionDossier

console = Console()


def print_banner():
    """Affiche la bannière d'en-tête umlStudio."""
    title = Text("◆ umlStudio ◆", style="bold cyan")
    subtitle = Text("Système de validation et de traçabilité d'architecture logicielle", style="dim italic")
    console.print(Panel(Text.assemble(title, "\n", subtitle), border_style="cyan", box=box.ROUNDED))


def render_rules_report(results: List[RuleResult], readiness_score: float) -> None:
    """Affiche le tableau d'évaluation des règles avec codes couleurs et badges."""
    print_banner()

    table = Table(
        title="Contrôle des 10 Règles Fondamentales & Intégrité",
        title_style="bold magenta",
        box=box.ROUNDED,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("Règle", style="bold white", width=10)
    table.add_column("Intitulé", style="white", ratio=3)
    table.add_column("Statut", justify="center", width=12)
    table.add_column("Diagnostic synthétique", style="dim white", ratio=4)
    table.add_column("Anomalies", justify="right", width=10)

    total_violations = 0
    errors_count = 0

    for r in results:
        v_count = len(r.violations)
        total_violations += v_count

        if r.passed:
            status_badge = "[bold green]PASS[/bold green]"
        elif r.severity == "WARNING":
            status_badge = "[bold yellow]WARN[/bold yellow]"
        elif r.severity == "INFO":
            status_badge = "[bold blue]INFO[/bold blue]"
        else:
            status_badge = "[bold red]FAIL[/bold red]"
            errors_count += 1

        v_count_str = f"[bold red]{v_count}[/bold red]" if v_count > 0 and r.severity == "ERROR" else (
            f"[yellow]{v_count}[/yellow]" if v_count > 0 else "[green]0[/green]"
        )

        table.add_row(r.rule_id, r.title, status_badge, r.summary, v_count_str)

    console.print(table)
    console.print()

    # Score de maturité (Readiness Score)
    score_color = "green" if readiness_score >= 90 else ("yellow" if readiness_score >= 60 else "red")
    score_msg = (
        "Dossier conforme et prêt pour validation de jalon !"
        if readiness_score == 100
        else ("Dossier en bonne voie mais des points bloquants subsistent." if readiness_score >= 60 else "Dossier incomplet : non prêt pour mise en production.")
    )

    console.print(
        Panel(
            f"[bold]Score de maturité de la conception :[/bold] [{score_color} bold]{readiness_score:.0f}%[/] — {score_msg}",
            border_style=score_color,
            box=box.ROUNDED,
        )
    )

    # Détails des violations
    all_violations = []
    for r in results:
        for v in r.violations:
            all_violations.append((r.rule_id, v))

    if all_violations:
        console.print("\n[bold red]Détail des anomalies à résoudre avant validation :[/bold red]\n")
        v_table = Table(box=box.SIMPLE_HEAD, expand=True, header_style="bold yellow")
        v_table.add_column("Règle", style="cyan", width=10)
        v_table.add_column("Fichier", style="bold magenta", width=22)
        v_table.add_column("Élément", style="bold white", width=12)
        v_table.add_column("Problème constaté & Recommandation", ratio=1)

        for rule_id, v in all_violations:
            item_display = v.item_id or "-"
            msg_text = Text()
            msg_text.append(v.message, style="white")
            if v.recommendation:
                msg_text.append("\n➜ Action : ", style="bold green")
                msg_text.append(v.recommendation, style="italic dim green")
            v_table.add_row(rule_id, v.file_name, item_display, msg_text)

        console.print(v_table)
    else:
        console.print("\n[bold green]✓ Aucune anomalie détectée : toutes les règles sont respectées ![/bold green]\n")


def render_matrix_report(matrix: TraceabilityReport) -> None:
    """Affiche la matrice de traçabilité dans le terminal."""
    print_banner()

    stats_text = (
        f"Exigences testées : [bold cyan]{matrix.tested_exigences}/{matrix.total_exigences}[/] ({matrix.coverage_tests_pct}%) | "
        f"Cas d'utilisation couverts par composants : [bold cyan]{matrix.covered_ucs}/{matrix.total_ucs}[/] ({matrix.coverage_ucs_pct}%)"
    )
    console.print(Panel(stats_text, title="Couverture de Traçabilité", border_style="cyan", box=box.ROUNDED))
    console.print()

    table = Table(
        title="Matrice de Traçabilité de Bout en Bout",
        box=box.ROUNDED,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("Obj.", style="dim", width=8)
    table.add_column("Exigence (EX)", style="bold white", width=12)
    table.add_column("Priorité", justify="center", width=10)
    table.add_column("Cas d'Usage (UC)", style="cyan", width=16)
    table.add_column("Composants (CMP)", style="magenta", width=18)
    table.add_column("Tests (TST)", style="green", width=16)
    table.add_column("Statut Tests", justify="center", width=14)

    for row in matrix.rows:
        cmps_str = ", ".join(row.composants_ids) if row.composants_ids else "[dim red]Aucun[/dim red]"
        tests_str = ", ".join(row.tests_ids) if row.tests_ids else "[dim red]Aucun[/dim red]"
        status_str = ", ".join(row.tests_statuts) if row.tests_statuts else "-"

        prio_color = "red" if row.exigence_priorite.lower() == "must" else ("yellow" if row.exigence_priorite.lower() == "should" else "blue")
        prio_text = f"[{prio_color}]{row.exigence_priorite}[/{prio_color}]"

        table.add_row(
            row.objectif_id,
            row.exigence_id,
            prio_text,
            row.cas_utilisation_id,
            cmps_str,
            tests_str,
            status_str,
        )

    console.print(table)


def render_stats_dashboard(dossier: ConceptionDossier) -> None:
    """Affiche le dashboard des statistiques du dossier de conception."""
    print_banner()

    proj_name = (dossier.cadrage.projet.nom if dossier.cadrage and dossier.cadrage.projet else "") or "Projet non nommé"
    proj_code = (dossier.cadrage.projet.code if dossier.cadrage and dossier.cadrage.projet else "") or "N/A"

    console.print(Panel(f"[bold cyan]{proj_name}[/] [dim]({proj_code})[/] — Répertoire : [italic]{dossier.root_path}[/]", box=box.ROUNDED))
    console.print()

    t = Table(box=box.ROUNDED, expand=True, title="Indicateurs Quantitatifs de Conception")
    t.add_column("Domaine", style="bold cyan")
    t.add_column("Indicateur", style="white")
    t.add_column("Valeur", justify="right", style="bold green")

    # Cadrage
    nb_obj = len(dossier.cadrage.objectifs) if dossier.cadrage else 0
    t.add_row("00-Cadrage", "Objectifs déclarés", str(nb_obj))

    # Exigences
    if dossier.exigences:
        nb_act = len(dossier.exigences.acteurs)
        nb_ex = len(dossier.exigences.exigences)
        nb_must = sum(1 for e in dossier.exigences.exigences if str(e.priorite).lower() == "must")
        nb_uc = len(dossier.exigences.cas_utilisation)
        t.add_row("01-Exigences", "Acteurs du système", str(nb_act))
        t.add_row("01-Exigences", "Exigences totales", str(nb_ex))
        t.add_row("01-Exigences", "Exigences critiques (Must)", f"[red]{nb_must}[/red]")
        t.add_row("01-Exigences", "Cas d'utilisation (UC)", str(nb_uc))

    # Architecture
    if dossier.architecture:
        nb_dec = len(dossier.architecture.decisions)
        nb_cmp = len(dossier.architecture.composants)
        nb_ent = len(dossier.architecture.entites)
        t.add_row("03-Architecture", "Décisions d'architecture (ADR)", str(nb_dec))
        t.add_row("03-Architecture", "Composants applicatifs", str(nb_cmp))
        t.add_row("03-Architecture", "Entités du domaine", str(nb_ent))

    # Plan
    if dossier.plan:
        nb_lots = len(dossier.plan.lots)
        nb_jalons = len(dossier.plan.jalons)
        t.add_row("04-Plan", "Lots de développement", str(nb_lots))
        t.add_row("04-Plan", "Jalons de validation", str(nb_jalons))

    # Risques
    if dossier.risques:
        nb_rsk = len(dossier.risques.risques)
        nb_dp = len(dossier.risques.donnees_personnelles)
        t.add_row("05-Risques", "Risques répertoriés", str(nb_rsk))
        t.add_row("05-Risques", "Traitements Données Personnelles (RGPD)", str(nb_dp))

    # Tests
    if dossier.tests:
        nb_tst = len(dossier.tests.tests)
        t.add_row("06-Tests", "Scénarios de tests définis", str(nb_tst))

    # Validations
    if dossier.validations:
        nb_val = len(dossier.validations.validations)
        t.add_row("Validations", "Entrées au registre SHA-256", str(nb_val))

    console.print(t)
