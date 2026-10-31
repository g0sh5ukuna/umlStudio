"""Tests du contrat d'API : lecture d'OpenAPI et diagramme de flux des opérations."""

import xml.etree.ElementTree as ET
from pathlib import Path

from umlstudio.core.loader import extract_openapi_operations, load_dossier
from umlstudio.reporters.diagrams import api_flow_mermaid, api_flow_svg

DOSSIER = Path("tests/fixtures/dossier_complet")


def _ops():
    return {op.operation_id: op for op in extract_openapi_operations(DOSSIER / "api")}


def test_lecture_methode_chemin_et_resume():
    op = _ops()["creerDemande"]
    assert (op.methode, op.chemin, op.resume) == ("POST", "/api/demandes/", "Déposer une demande")


def test_securite_publique_globale_et_alternatives():
    ops = _ops()
    assert ops["creerDemande"].securite == ["Public"]
    assert ops["lireDemande"].securite == ["JWT (Bearer)"]
    assert ops["confirmerDemande"].securite == ["Cookie sessionid", "OAuth2 (demandes:ecrire)"]


def test_champs_requis_et_optionnels_depuis_un_schema_reference():
    champs = {c.nom: c for c in _ops()["creerDemande"].champs}
    assert {n for n, c in champs.items() if c.requis} == {"nom", "telephone", "consentement"}
    assert champs["piece"].type == "fichier" and not champs["piece"].requis
    assert champs["niveaux"].type == "liste de string"
    assert champs["nom"].emplacement == "corps"


def test_parametres_de_chemin_herites_du_chemin():
    champs = {c.nom: c for c in _ops()["confirmerDemande"].champs}
    assert champs["id"].emplacement == "chemin" and champs["id"].requis
    assert champs["code"].requis


def test_reponses_separees_en_succes_et_erreurs():
    op = _ops()["creerDemande"]
    assert [r.code for r in op.succes] == ["201"]
    assert [(r.code, r.description) for r in op.erreurs] == [("400", "Champ requis manquant"), ("429", "Trop de dépôts")]


def test_stockage_declare_vide_ou_absent():
    ops = _ops()
    assert ops["creerDemande"].stocke == ["ENT-01", "ENT-03"]
    assert ops["lireDemande"].stocke == []
    assert ops["confirmerDemande"].stocke is None


def test_operation_sans_operation_id_garde_methode_et_chemin_comme_identifiant():
    assert "GET /api/sante/" in _ops()


def test_le_dossier_charge_les_operations_et_garde_les_identifiants_pour_la_regle_4():
    dossier, _ = load_dossier(DOSSIER)
    assert len(dossier.operations) == 5
    assert "creerDemande" in dossier.openapi_endpoints


def test_le_flux_svg_enchaine_les_operations_du_cas_d_utilisation():
    dossier, _ = load_dossier(DOSSIER)
    uc = dossier.exigences.cas_utilisation[0]
    svg = api_flow_svg(uc, dossier)
    texte = "".join(ET.fromstring(svg).itertext())
    for attendu in ("POST", "/api/demandes/", "PATCH", "Public", "OAuth2", "nom", "telephone",
                    "400", "Champ requis manquant", "Stockage non déclaré", "introuvable", "Demande enregistrée"):
        assert attendu in texte, attendu
    # L'entité stockée est nommée, pas seulement identifiée.
    nom_entite = dossier.architecture.entites[0].nom
    assert nom_entite and nom_entite in texte


def test_un_cas_sans_endpoint_n_a_pas_de_flux():
    dossier, _ = load_dossier(DOSSIER)
    uc = dossier.exigences.cas_utilisation[0].model_copy(update={"endpoints": []})
    assert api_flow_svg(uc, dossier) == ""
    assert api_flow_mermaid(uc, dossier) == ""


def test_le_flux_mermaid_montre_succes_et_erreurs():
    dossier, _ = load_dossier(DOSSIER)
    code = api_flow_mermaid(dossier.exigences.cas_utilisation[0], dossier)
    assert code.startswith("flowchart TD")
    assert '-- "201 Demande créée" -->' in code
    assert "-.->" in code
