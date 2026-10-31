"""Interface en ligne de commande (CLI) moderne pour umlStudio."""

import json
import shutil
import stat
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from . import __version__
from .core.loader import find_conception_root, load_dossier
from .core.rules import evaluate_all_rules
from .core.integrity import compute_sha256, sign_document
from .reporters.console import (
    console,
    print_banner,
    render_rules_report,
    render_matrix_report,
    render_stats_dashboard,
)
from .reporters.matrix import build_traceability_matrix
from .reporters.html import generate_html_report
from .reporters.markdown import generate_markdown_report
from .reporters.spec_doc import generate_spec_markdown, generate_spec_html

app = typer.Typer(
    name="umlstudio",
    help="umlStudio - Outil d'ingénierie, de validation et de traçabilité pour dossiers de conception logicielle.",
    no_args_is_help=True,
)


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]umlStudio[/bold cyan] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Afficher la version."
    ),
):
    pass


@app.command(name="check")
def check_cmd(
    target: Optional[Path] = typer.Argument(
        None,
        help="Chemin vers le dossier de conception (défaut: dossier courant ou modeles/conception).",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Mode strict : échoue (code retour 1) même pour les simples avertissements.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Affiche le résultat en JSON brut (utile pour CI/CD).",
    ),
):
    """Valide l'ensemble du dossier de conception selon les 10 Règles Fondamentales et l'intégrité SHA-256."""
    dossier, load_errors = load_dossier(target)

    if load_errors and not json_output:
        for err in load_errors:
            console.print(f"[bold red]Erreur de chargement [{err.file_name}]:[/bold red] {err.message}")

    results = evaluate_all_rules(dossier)

    # Calcul du score
    total_rules = len(results)
    passed_rules = sum(1 for r in results if r.passed)
    readiness_score = (passed_rules / total_rules) * 100 if total_rules > 0 else 0.0

    if json_output:
        data = {
            "version": __version__,
            "root_path": str(dossier.root_path),
            "readiness_score": readiness_score,
            "rules": [r.model_dump() for r in results],
            "load_errors": [{"file": e.file_name, "message": e.message} for e in load_errors],
        }
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        render_rules_report(results, readiness_score)

    has_errors = any(not r.passed and r.severity == "ERROR" for r in results) or bool(load_errors)
    has_warnings = any(not r.passed and r.severity == "WARNING" for r in results)

    if has_errors or (strict and has_warnings):
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


# Alias validate -> check
@app.command(name="validate", hidden=True)
def validate_alias(
    target: Optional[Path] = typer.Argument(None),
    strict: bool = typer.Option(False, "--strict", "-s"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Alias pour 'check'."""
    check_cmd(target=target, strict=strict, json_output=json_output)


@app.command(name="matrix")
def matrix_cmd(
    target: Optional[Path] = typer.Argument(
        None,
        help="Chemin vers le dossier de conception.",
    ),
):
    """Affiche la matrice de traçabilité de bout en bout (Objectifs -> Exigences -> UCs -> Composants -> Tests)."""
    dossier, _ = load_dossier(target)
    matrix = build_traceability_matrix(dossier)
    render_matrix_report(matrix)


@app.command(name="stats")
def stats_cmd(
    target: Optional[Path] = typer.Argument(
        None,
        help="Chemin vers le dossier de conception.",
    ),
):
    """Affiche les métriques et indicateurs de volume du projet."""
    dossier, _ = load_dossier(target)
    render_stats_dashboard(dossier)


@app.command(name="report")
def report_cmd(
    target: Optional[Path] = typer.Argument(
        None,
        help="Chemin vers le dossier de conception.",
    ),
    format: str = typer.Option(
        "html",
        "--format",
        "-f",
        help="Format du rapport : 'html' ou 'md'.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Chemin du fichier de destination.",
    ),
):
    """Génère un rapport exécutif complet de haute qualité (HTML autonome ou Markdown)."""
    dossier, _ = load_dossier(target)
    rules = evaluate_all_rules(dossier)

    fmt = format.lower().strip()
    if fmt == "html":
        out_file = output or (dossier.root_path / "rapport-conception.html")
        generate_html_report(dossier, rules, out_file)
        console.print(f"[bold green]✓ Rapport HTML généré avec succès :[/bold green] [cyan]{out_file}[/cyan]")
    elif fmt in ["md", "markdown"]:
        out_file = output or (dossier.root_path / "rapport-conception.md")
        generate_markdown_report(dossier, rules, out_file)
        console.print(f"[bold green]✓ Rapport Markdown généré avec succès :[/bold green] [cyan]{out_file}[/cyan]")
    else:
        console.print(f"[bold red]Format non supporté : '{format}'. Utilisez 'html' ou 'md'.[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="doc")
def doc_cmd(
    target: Optional[Path] = typer.Argument(
        None,
        help="Chemin vers le dossier de conception.",
    ),
    format: str = typer.Option(
        "md",
        "--format",
        "-f",
        help="Format : 'md' (par défaut, idéal pour README/Wiki) ou 'html' (fiche web avec navigation, prête pour impression PDF).",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Chemin du fichier de destination (défaut: specification-projet.md ou specification-projet.html).",
    ),
):
    """Génère le Dossier de Spécifications Développeur complet (vue macro 'en gros' et détails techniques : classes, champs requis, scénarios pas-à-pas, sécurité, tests BDD)."""
    dossier, _ = load_dossier(target)
    fmt = format.lower().strip()
    if fmt in ["md", "markdown"]:
        out_file = output or (dossier.root_path / "specification-projet.md")
        generate_spec_markdown(dossier, out_file)
        console.print(f"[bold green]✓ Document de spécifications Markdown généré avec succès :[/bold green] [cyan]{out_file}[/cyan]")
    elif fmt == "html":
        out_file = output or (dossier.root_path / "specification-projet.html")
        generate_spec_html(dossier, out_file)
        console.print(f"[bold green]✓ Document de spécifications HTML généré avec succès :[/bold green] [cyan]{out_file}[/cyan]")
    else:
        console.print(f"[bold red]Format non supporté : '{format}'. Utilisez 'md' ou 'html'.[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="spec", hidden=True)
def spec_alias(
    target: Optional[Path] = typer.Argument(None),
    format: str = typer.Option("md", "--format", "-f"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Alias pour 'doc'."""
    doc_cmd(target=target, format=format, output=output)


@app.command(name="sign")
def sign_cmd(
    document: str = typer.Argument(
        ...,
        help="Nom du fichier à signer (ex: 00-cadrage.yaml).",
    ),
    target: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Chemin vers le dossier de conception.",
    ),
    author: str = typer.Option(
        "",
        "--author",
        "-a",
        help="Nom du validateur.",
    ),
    role: str = typer.Option(
        "",
        "--role",
        "-r",
        help="Rôle du validateur (ex: Commanditaire, Lead Tech).",
    ),
    evidence: str = typer.Option(
        "",
        "--evidence",
        "-e",
        help="Lien ou identifiant de la preuve d'approbation (ex: PR #42).",
    ),
    version: str = typer.Option(
        "0.1.0",
        "--version",
        "-v",
        help="Version du document validée.",
    ),
):
    """Calcule l'empreinte SHA-256 d'un fichier et l'inscrit dans validations.yaml."""
    root = find_conception_root(target)
    success, msg = sign_document(
        dossier_path=root,
        document_rel_name=document,
        author_name=author,
        author_role=role,
        evidence_url=evidence,
        version=version,
    )
    if success:
        console.print(f"[bold green]✓ {msg}[/bold green]")
    else:
        console.print(f"[bold red]✗ {msg}[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="sign-all")
def sign_all_cmd(
    target: Optional[Path] = typer.Argument(
        None,
        help="Chemin vers le dossier de conception.",
    ),
    author: str = typer.Option(
        "",
        "--author",
        "-a",
        help="Nom du validateur.",
    ),
    role: str = typer.Option(
        "",
        "--role",
        "-r",
        help="Rôle du validateur.",
    ),
    evidence: str = typer.Option(
        "",
        "--evidence",
        "-e",
        help="Preuve d'approbation.",
    ),
):
    """Signe et calcule les hash SHA-256 de tous les fichiers YAML du dossier de conception."""
    root = find_conception_root(target)
    files = [
        "00-cadrage.yaml",
        "01-exigences.yaml",
        "02-glossaire.yaml",
        "03-architecture.yaml",
        "04-plan.yaml",
        "05-risques.yaml",
        "06-tests.yaml",
    ]

    count = 0
    for f in files:
        if (root / f).is_file():
            success, msg = sign_document(
                dossier_path=root,
                document_rel_name=f,
                author_name=author,
                author_role=role,
                evidence_url=evidence,
            )
            if not success:
                console.print(f"[bold red]✗ {msg}[/bold red]")
                raise typer.Exit(code=1)
            console.print(f"[green]✓ {msg}[/green]")
            count += 1
    console.print(f"\n[bold green]✓ {count} document(s) signés avec succès dans validations.yaml.[/bold green]")


def _template_source() -> Path:
    """Modèles embarqués dans le wheel, ou ceux du dépôt en installation éditable."""
    packaged = Path(__file__).resolve().parent / "modeles" / "conception"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parent.parent.parent / "modeles" / "conception"


@app.command(name="init")
def init_cmd(
    destination: Path = typer.Argument(
        ...,
        help="Dossier cible où initialiser le dossier de conception.",
    ),
    name: str = typer.Option(
        "",
        "--name",
        "-n",
        help="Nom du projet.",
    ),
    code: str = typer.Option(
        "",
        "--code",
        "-c",
        help="Code court du projet (ex: MON-PROJET).",
    ),
):
    """Initialise un nouveau dossier de conception complet à partir des modèles officiels umlStudio."""
    template_source = _template_source()

    if not template_source.exists():
        console.print(f"[bold red]Erreur : modèles introuvables dans {template_source}[/bold red]")
        raise typer.Exit(code=1)

    if destination.exists() and any(destination.iterdir()):
        console.print(f"[bold yellow]Attention : le dossier cible '{destination}' n'est pas vide.[/bold yellow]")
        if not typer.confirm("Voulez-vous continuer et écraser/ajouter les modèles ?"):
            raise typer.Abort()

    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template_source, destination, dirs_exist_ok=True)

    # Assurer les droits d'écriture sur les fichiers copiés
    for item in destination.rglob("*"):
        if item.is_file():
            item.chmod(item.stat().st_mode | stat.S_IWUSR | stat.S_IRUSR)

    # Personnalisation de 00-cadrage.yaml si nom ou code fourni
    cadrage_path = destination / "00-cadrage.yaml"
    if cadrage_path.exists() and (name or code):
        content = cadrage_path.read_text(encoding="utf-8")
        if name:
            content = content.replace('nom: ""', f'nom: "{name}"', 1)
        if code:
            content = content.replace('code: ""', f'code: "{code}"', 1)
        cadrage_path.write_text(content, encoding="utf-8")

    console.print(f"[bold green]✓ Dossier de conception initialisé avec succès dans :[/bold green] [cyan]{destination}[/cyan]")
    console.print("[dim]Remplissez maintenant les fichiers dans l'ordre, de 00-cadrage.yaml à 06-tests.yaml.[/dim]")
