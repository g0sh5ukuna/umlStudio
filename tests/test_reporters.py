"""Tests pour les générateurs de rapports HTML et Markdown."""

from pathlib import Path
from umlstudio.models.dossier import ConceptionDossier
from umlstudio.models.common import DocumentHeader
from umlstudio.models.cadrage import CadrageDocument, ProjectInfo, ProjectPerson
from umlstudio.core.rules import evaluate_all_rules
from umlstudio.reporters.html import generate_html_report
from umlstudio.reporters.markdown import generate_markdown_report


def test_markdown_and_html_generation(tmp_path: Path):
    dossier = ConceptionDossier(
        root_path=tmp_path,
        cadrage=CadrageDocument(
            document=DocumentHeader(type="cadrage"),
            projet=ProjectInfo(
                nom="Projet Étoile",
                code="ETOILE",
                commanditaire=ProjectPerson(nom="Directeur", role="Sponsor"),
            ),
            contexte="Contexte de test",
        ),
    )

    rules = evaluate_all_rules(dossier)

    md_path = tmp_path / "rapport.md"
    generate_markdown_report(dossier, rules, md_path)
    assert md_path.is_file()
    content_md = md_path.read_text(encoding="utf-8")
    assert "Projet Étoile" in content_md
    assert "ETOILE" in content_md
    assert "REGLE-01" in content_md

    html_path = tmp_path / "rapport.html"
    generate_html_report(dossier, rules, html_path)
    assert html_path.is_file()
    content_html = html_path.read_text(encoding="utf-8")
    assert "Projet Étoile" in content_html
    assert "REGLE-01" in content_html


def test_rapports_html_echappent_le_contenu_du_dossier(tmp_path: Path):
    from umlstudio.reporters.spec_doc import generate_spec_html

    charge = "<script>alert(1)</script>"
    dossier = ConceptionDossier(
        root_path=tmp_path,
        cadrage=CadrageDocument(
            document=DocumentHeader(type="cadrage"),
            projet=ProjectInfo(nom=charge, code="XSS"),
            contexte=charge,
        ),
    )

    html_path = tmp_path / "rapport.html"
    generate_html_report(dossier, evaluate_all_rules(dossier), html_path)
    rapport = html_path.read_text(encoding="utf-8")
    assert charge not in rapport
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rapport

    spec = generate_spec_html(dossier, tmp_path / "spec.html")
    assert charge not in spec
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in spec
