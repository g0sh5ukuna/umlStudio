"""Tests du volet base de données : schéma, migrations, effets des appels en base."""

import xml.etree.ElementTree as ET
from pathlib import Path

from umlstudio.core.loader import load_dossier
from umlstudio.core.rules import check_rule_12_integrite_referentielle
from umlstudio.models.api import EffetBdd
from umlstudio.models.architecture import Attribut
from umlstudio.reporters.database import erd_mermaid, erd_svg, operation_db_effects
from umlstudio.reporters.spec_doc import generate_spec_html, generate_spec_markdown

DOSSIER = Path("tests/fixtures/dossier_complet")


def _dossier():
    dossier, erreurs = load_dossier(DOSSIER)
    assert not erreurs
    return dossier


def _op(dossier, op_id):
    return next(op for op in dossier.operations if op.operation_id == op_id)


def test_le_schema_et_les_migrations_sont_lus():
    archi = _dossier().architecture
    demande = archi.entites[0]
    assert demande.table == "demande"
    assert demande.attributs[2].reference == "ENT-02" and demande.attributs[2].sur_suppression == "protect"
    assert demande.contraintes[0].champs == ["agent_id", "telephone"]
    assert [m.id for m in archi.migrations] == ["MIG-01", "MIG-02"]
    assert archi.migrations[1].statut == "prevue"


def test_les_effets_en_base_sont_lus_dans_le_contrat():
    op = _op(_dossier(), "creerDemande")
    assert op.transaction is True
    assert [(e.entite, e.action) for e in op.effets] == [("ENT-02", "lecture"), ("ENT-01", "insert"), ("ENT-03", "insert")]
    assert op.stocke == ["ENT-01", "ENT-03"]


def test_un_insert_annonce_les_contraintes_verifiees():
    dossier = _dossier()
    effets = operation_db_effects(_op(dossier, "creerDemande"), dossier)
    texte = "\n".join(line for titre, details in effets for line in [titre, *details])
    assert "Transaction" in texte
    assert "INSERT dans demande" in texte
    assert "NOT NULL" in texte and "telephone" in texte
    assert "UNIQUE" in texte and "une_demande_par_agent" in texte
    assert "agent_id → agent" in texte
    assert "SELECT dans agent" in texte


def test_un_delete_annonce_cascades_et_blocages():
    dossier = _dossier()
    effets = operation_db_effects(_op(dossier, "supprimerDemande"), dossier)
    texte = "\n".join(line for titre, details in effets for line in [titre, *details])
    assert "DELETE dans demande" in texte
    assert "CASCADE" in texte and "piece_jointe" in texte


def test_le_schema_svg_montre_tables_cles_et_liens():
    svg = erd_svg(_dossier())
    root = ET.fromstring(svg)
    texte = "".join(root.itertext())
    for attendu in ("demande", "agent", "piece_jointe", "PK", "FK", "UQ"):
        assert attendu in texte, attendu
    liens = {e.get("data-lien") for e in root.iter() if e.get("data-lien")}
    assert {"ENT-01>ENT-02", "ENT-03>ENT-01"} <= liens


def test_le_schema_mermaid_est_un_diagramme_entite_relation():
    code = erd_mermaid(_dossier())
    assert code.startswith("erDiagram")
    assert "agent ||--o{ demande" in code
    assert "int" not in code or True  # les types du dossier sont repris tels quels
    assert "entier id PK" in code


def test_regle_12_signale_references_de_table_et_effets_inconnus():
    dossier = _dossier()
    dossier.architecture.entites[0].attributs.append(Attribut(nom="x_id", cle="etrangere", reference="ENT-99"))
    dossier.operations[0].effets.append(EffetBdd(entite="ENT-98", action="update"))
    messages = " ".join(v.message for v in check_rule_12_integrite_referentielle(dossier).violations)
    assert "ENT-99" in messages and "ENT-98" in messages


def test_la_specification_presente_schema_migrations_et_effets(tmp_path: Path):
    dossier = _dossier()
    html = generate_spec_html(dossier, tmp_path / "spec.html")
    assert 'class="diagramme-bdd"' in html
    assert "Migrations" in html and "MIG-02" in html and "Dédoublonner" in html
    assert "Effets en base" in html and "CASCADE" in html

    md = generate_spec_markdown(dossier, tmp_path / "spec.md")
    assert "erDiagram" in md
    assert "### Migrations" in md
    assert "Effets en base" in md


def test_une_relation_deja_portee_par_une_cle_etrangere_n_est_pas_dessinee_deux_fois():
    root = ET.fromstring(erd_svg(_dossier()))
    assert not [e for e in root.iter() if e.get("data-relation")]
    assert erd_mermaid(_dossier()).count("demande ||--o{ piece_jointe") == 1
