"""Tests des diagrammes : couloirs par cas d'utilisation et vue de bout en bout."""

import xml.etree.ElementTree as ET
from pathlib import Path

from umlstudio.models.dossier import ConceptionDossier
from umlstudio.models.common import DocumentHeader
from umlstudio.models.exigences import ExigencesDocument, CasUtilisation, Acteur
from umlstudio.models.architecture import ArchitectureDocument, Composant
from umlstudio.reporters.diagrams import (
    assign_lanes,
    architecture_mermaid,
    architecture_svg,
    swimlane_mermaid,
    swimlane_svg,
)

ACTEURS = {
    "ACT-01": Acteur(id="ACT-01", nom="Parent"),
    "ACT-02": Acteur(id="ACT-02", nom="Répétiteur"),
    "ACT-03": Acteur(id="ACT-03", nom="Personnel"),
    "ACT-04": Acteur(id="ACT-04", nom="FedaPay", type="systeme"),
}


def _uc(steps, secondaires=None) -> CasUtilisation:
    return CasUtilisation(
        id="UC-06",
        nom="Débloquer le contact",
        acteur_principal="ACT-02",
        acteurs_secondaires=secondaires or [],
        scenario_nominal=steps,
    )


def test_chaque_etape_va_dans_le_couloir_de_son_sujet():
    steps = [
        "1. Le répétiteur choisit une demande",
        "2. Le système débite un crédit",
        "3. Il révèle le contact",
        "4. Le personnel prévient le parent par WhatsApp",
    ]
    assert assign_lanes(steps, list(ACTEURS.values()), default="Répétiteur") == [
        "Répétiteur",
        "Système",
        "Système",
        "Personnel",
    ]


def test_le_couloir_svg_montre_les_acteurs_et_les_etapes():
    svg = swimlane_svg(_uc(["1. Le répétiteur choisit une demande", "2. Le système débite un crédit"]), ACTEURS)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    texte = "".join(root.itertext())
    for attendu in ("Répétiteur", "Système", "choisit", "débite"):
        assert attendu in texte


def test_un_acteur_cite_sans_etre_declare_obtient_son_couloir():
    svg = swimlane_svg(_uc(["1. Le répétiteur choisit", "2. Le personnel prévient le parent"]), ACTEURS)
    assert "Personnel" in "".join(ET.fromstring(svg).itertext())


def test_un_scenario_vide_ne_produit_pas_de_diagramme():
    assert swimlane_svg(_uc(["1. ", ""]), ACTEURS) == ""
    assert swimlane_mermaid(_uc([]), ACTEURS) == ""


def test_le_svg_echappe_le_contenu_du_dossier():
    svg = swimlane_svg(_uc(["1. Le répétiteur saisit <script>alert(1)</script> & valide"]), ACTEURS)
    assert "<script>" not in svg
    ET.fromstring(svg)


def test_le_couloir_mermaid_est_un_diagramme_de_sequence():
    code = swimlane_mermaid(_uc(["1. Le répétiteur choisit", "2. Le système débite ; puis révèle"]), ACTEURS)
    assert code.startswith("sequenceDiagram")
    assert "participant" in code
    assert ";" not in code


def _dossier(tmp_path: Path) -> ConceptionDossier:
    return ConceptionDossier(
        root_path=tmp_path,
        exigences=ExigencesDocument(
            document=DocumentHeader(type="exigences"),
            acteurs=list(ACTEURS.values()),
            cas_utilisation=[
                CasUtilisation(id="UC-05", nom="Acheter un pack", acteur_principal="ACT-02", acteurs_secondaires=["ACT-04"]),
            ],
        ),
        architecture=ArchitectureDocument(
            document=DocumentHeader(type="architecture"),
            composants=[
                Composant(id="CMP-01", nom="Front Next", couche="presentation", cas_utilisation=["UC-05"], depend_de=["CMP-02"]),
                Composant(id="CMP-02", nom="Intégration FedaPay", couche="application", cas_utilisation=["UC-05"], depend_de=["CMP-03"]),
                Composant(id="CMP-03", nom="PostgreSQL", couche="donnees"),
            ],
        ),
    )


def test_la_vue_de_bout_en_bout_relie_acteurs_composants_et_externes(tmp_path: Path):
    svg = architecture_svg(_dossier(tmp_path))
    root = ET.fromstring(svg)
    texte = "".join(root.itertext())
    for attendu in ("Répétiteur", "Front Next", "Intégration FedaPay", "PostgreSQL", "FedaPay"):
        assert attendu in texte
    liens = [e for e in root.iter() if e.tag.endswith("path") and e.get("data-lien")]
    assert {e.get("data-lien") for e in liens} >= {"ACT-02>CMP-01", "CMP-01>CMP-02", "CMP-02>CMP-03", "ACT-04>CMP-02"}


def test_la_vue_mermaid_reprend_les_memes_liens(tmp_path: Path):
    code = architecture_mermaid(_dossier(tmp_path))
    assert code.startswith("flowchart LR")
    assert "ACT_02 --> CMP_01" in code
    assert "CMP_01 --> CMP_02" in code


def test_sans_architecture_pas_de_vue(tmp_path: Path):
    assert architecture_svg(ConceptionDossier(root_path=tmp_path)) == ""


def test_des_composants_sans_nom_ne_produisent_pas_de_vue(tmp_path: Path):
    dossier = ConceptionDossier(
        root_path=tmp_path,
        architecture=ArchitectureDocument(
            document=DocumentHeader(type="architecture"),
            composants=[Composant(id="CMP-01", nom="")],
        ),
    )
    assert architecture_svg(dossier) == ""
    assert architecture_mermaid(dossier) == ""
