"""Tests unitaires pour la génération du document de spécifications développeur (umlstudio doc)."""

from pathlib import Path
from typer.testing import CliRunner

from umlstudio.cli import app
from umlstudio.core.loader import load_dossier
from umlstudio.reporters.spec_doc import generate_spec_markdown, generate_spec_html

runner = CliRunner()


def test_generate_spec_markdown_and_html(tmp_path: Path):
    dossier, _ = load_dossier(Path("modeles/conception"))

    md_path = tmp_path / "spec.md"
    content_md = generate_spec_markdown(dossier, md_path)
    assert md_path.exists()
    assert "# Dossier de Spécifications & Conception Logicielle" in content_md
    assert "## 7. Modèle de Données : Classes & Champs Requis" in content_md
    assert "## 8. Volet Sécurité & Protection des Données (RGPD)" in content_md
    assert "## 9. Cahier de Recette & Scénarios de Tests (BDD)" in content_md
    assert "## 10. Plan de Réalisation & Lots Développeurs" in content_md

    html_path = tmp_path / "spec.html"
    content_html = generate_spec_html(dossier, html_path)
    assert html_path.exists()
    assert "Dossier de Spécifications" in content_html
    assert "Classes & Champs Requis" in content_html
    assert "Volet Sécurité & Données Personnelles" in content_html


def test_cli_doc_command(tmp_path: Path):
    out_md = tmp_path / "dev_spec.md"
    res_md = runner.invoke(app, ["doc", "modeles/conception", "--format", "md", "--output", str(out_md)])
    assert res_md.exit_code == 0
    assert out_md.exists()

    out_html = tmp_path / "dev_spec.html"
    res_html = runner.invoke(app, ["doc", "modeles/conception", "--format", "html", "--output", str(out_html)])
    assert res_html.exit_code == 0
    assert out_html.exists()

    # Test alias spec
    res_alias = runner.invoke(app, ["spec", "modeles/conception", "--format", "md", "--output", str(tmp_path / "alias.md")])
    assert res_alias.exit_code == 0
    assert (tmp_path / "alias.md").exists()
