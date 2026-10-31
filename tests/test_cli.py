"""Tests d'intégration end-to-end pour la CLI umlStudio."""

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner
from umlstudio.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "umlStudio version 0.1.0" in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout
    assert "matrix" in result.stdout
    assert "report" in result.stdout
    assert "stats" in result.stdout
    assert "sign" in result.stdout


def test_cli_stats_on_modeles():
    result = runner.invoke(app, ["stats", "modeles/conception"])
    assert result.exit_code == 0
    assert "00-Cadrage" in result.stdout
    assert "01-Exigences" in result.stdout


def test_cli_matrix_on_modeles():
    result = runner.invoke(app, ["matrix", "modeles/conception"])
    assert result.exit_code == 0
    assert "Matrice de Traçabilité de Bout en Bout" in result.stdout


def test_cli_check_json():
    result = runner.invoke(app, ["check", "modeles/conception", "--json"])
    # Doit retourner un JSON valide contenant les règles
    assert '"readiness_score"' in result.stdout
    assert '"rules"' in result.stdout


def test_cli_init_and_sign(tmp_path: Path):
    target = tmp_path / "nouveau_projet"
    # 1. Test init
    res_init = runner.invoke(app, ["init", str(target), "--name", "TestApp", "--code", "TST-APP"])
    assert res_init.exit_code == 0
    assert (target / "00-cadrage.yaml").exists()

    # 2. Test sign
    res_sign = runner.invoke(app, [
        "sign",
        "00-cadrage.yaml",
        "--path", str(target),
        "--author", "Josué",
        "--role", "Architecte",
        "--evidence", "PR #1",
    ])
    assert res_sign.exit_code == 0
    assert "Validation mise à jour pour '00-cadrage.yaml'" in res_sign.stdout or "Validation enregistrée pour '00-cadrage.yaml'" in res_sign.stdout

    # Vérifier que validations.yaml a bien le hash calculé
    validations_content = (target / "validations.yaml").read_text(encoding="utf-8")
    assert "sha256:" in validations_content
    assert "Josué" in validations_content


def test_cli_report(tmp_path: Path):
    report_html = tmp_path / "rapport.html"
    res = runner.invoke(app, ["report", "modeles/conception", "--format", "html", "--output", str(report_html)])
    assert res.exit_code == 0
    assert report_html.exists()
    assert "Score de Maturité" in report_html.read_text(encoding="utf-8")


def test_cli_check_sur_modele_vierge_signale_le_contenu_vide(tmp_path: Path):
    target = tmp_path / "vierge"
    assert runner.invoke(app, ["init", str(target)]).exit_code == 0

    result = runner.invoke(app, ["check", str(target), "--json"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    echecs = {r["rule_id"] for r in data["rules"] if not r["passed"]}
    assert {"REGLE-01", "REGLE-02", "REGLE-03", "REGLE-05", "REGLE-06"} <= echecs


def test_cli_sign_refuse_sans_preuve(tmp_path: Path):
    target = tmp_path / "projet"
    runner.invoke(app, ["init", str(target)])
    res = runner.invoke(app, ["sign", "00-cadrage.yaml", "--path", str(target), "--author", "Alice"])
    assert res.exit_code == 1
    assert "preuve" in res.stdout


def test_wheel_installe_peut_initialiser_un_dossier(tmp_path: Path):
    hatchling_wheel = pytest.importorskip("hatchling.builders.wheel")
    racine = Path(__file__).resolve().parent.parent
    wheel = Path(next(iter(hatchling_wheel.WheelBuilder(str(racine)).build(directory=str(tmp_path / "dist")))))

    site = tmp_path / "site"
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(site)

    cible = tmp_path / "depuis-wheel"
    code = "import sys; from umlstudio.cli import app; sys.argv = ['umlstudio', 'init', sys.argv[1]]; app()"
    res = subprocess.run(
        [sys.executable, "-c", code, str(cible)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(site)},
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert (cible / "00-cadrage.yaml").is_file()
