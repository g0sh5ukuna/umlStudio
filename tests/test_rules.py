"""Tests unitaires pour chacune des 10 règles fondamentales et les 2 contrôles d'intégrité."""

from pathlib import Path
import pytest

from umlstudio.models.dossier import ConceptionDossier
from umlstudio.models.common import DocumentHeader, DocumentStatus
from umlstudio.models.cadrage import CadrageDocument, Perimetre, Objectif
from umlstudio.models.exigences import ExigencesDocument, Exigence, CasUtilisation, Acteur
from umlstudio.models.glossaire import GlossaireDocument, Terme
from umlstudio.models.architecture import ArchitectureDocument, Composant, Entite, Attribut
from umlstudio.models.plan import PlanDocument, Lot
from umlstudio.models.risques import RisquesDocument, Risque, DonneePersonnelle
from umlstudio.models.tests import TestsDocument, TestItem
from umlstudio.models.validations import ValidationsDocument, ValidationEntry

from umlstudio.core.rules import (
    check_rule_1_exigences_mesurables,
    check_rule_2_exigence_liee_test,
    check_rule_3_uc_lie_acteur_et_exigence,
    check_rule_4_openapi_endpoints_lies_uc,
    check_rule_5_uc_couvert_par_composant,
    check_rule_6_glossaire_et_synonymes,
    check_rule_7_risques_responsable_et_mitigation,
    check_rule_8_donnees_personnelles_conformite,
    check_rule_9_cycle_dependances_plan,
    check_rule_10_perimetre_exclu_non_vide,
    check_rule_11_integrite_validations,
    check_rule_12_integrite_referentielle,
)


@pytest.fixture
def empty_dossier(tmp_path: Path) -> ConceptionDossier:
    return ConceptionDossier(root_path=tmp_path)


def test_rule_1_mesure_verifiable(empty_dossier: ConceptionDossier):
    # Invalide : mesure vide
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        exigences=[Exigence(id="EX-01", enonce="Le système enregistre la demande", mesure="")],
    )
    res = check_rule_1_exigences_mesurables(empty_dossier)
    assert not res.passed
    assert len(res.violations) == 1

    # Valide : mesure précise
    empty_dossier.exigences.exigences[0].mesure = "temps de réponse < 200 ms au 95e centile"
    res = check_rule_1_exigences_mesurables(empty_dossier)
    assert res.passed
    assert len(res.violations) == 0


def test_rule_2_exigence_liee_test(empty_dossier: ConceptionDossier):
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        exigences=[Exigence(id="EX-01", enonce="Le système enregistre", mesure="mesure 1")],
    )
    empty_dossier.tests = TestsDocument(
        document=DocumentHeader(type="tests"),
        tests=[],
    )
    # Sans test lié -> échec
    res = check_rule_2_exigence_liee_test(empty_dossier)
    assert not res.passed

    # Avec test lié -> succès
    empty_dossier.tests.tests.append(TestItem(id="TST-01", exigences=["EX-01"], quand="l'agent soumet", alors="la demande est enregistrée"))
    res = check_rule_2_exigence_liee_test(empty_dossier)
    assert res.passed


def test_rule_3_uc_liaisons(empty_dossier: ConceptionDossier):
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        cas_utilisation=[
            CasUtilisation(
                id="UC-01",
                nom="Soumettre une demande",
                acteur_principal="",
                exigences=[],
                scenario_nominal=["1. L'agent soumet la demande"],
            )
        ],
    )
    res = check_rule_3_uc_lie_acteur_et_exigence(empty_dossier)
    assert not res.passed
    assert len(res.violations) == 2  # manque acteur + manque exigence

    empty_dossier.exigences.cas_utilisation[0].acteur_principal = "ACT-01"
    empty_dossier.exigences.cas_utilisation[0].exigences = ["EX-01"]
    res = check_rule_3_uc_lie_acteur_et_exigence(empty_dossier)
    assert res.passed


def test_rule_4_openapi_endpoints(empty_dossier: ConceptionDossier):
    empty_dossier.openapi_endpoints = ["createItem", "deleteItem"]
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        cas_utilisation=[CasUtilisation(id="UC-01", endpoints=["createItem"])],
    )
    # deleteItem est orphelin
    res = check_rule_4_openapi_endpoints_lies_uc(empty_dossier)
    assert not res.passed
    assert res.violations[0].item_id == "deleteItem"

    # Ajout du second endpoint
    empty_dossier.exigences.cas_utilisation[0].endpoints.append("deleteItem")
    res = check_rule_4_openapi_endpoints_lies_uc(empty_dossier)
    assert res.passed


def test_rule_5_uc_couvert_par_composant(empty_dossier: ConceptionDossier):
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        cas_utilisation=[CasUtilisation(id="UC-01")],
    )
    empty_dossier.architecture = ArchitectureDocument(
        document=DocumentHeader(type="architecture"),
        composants=[],
    )
    res = check_rule_5_uc_couvert_par_composant(empty_dossier)
    assert not res.passed

    empty_dossier.architecture.composants.append(Composant(id="CMP-01", nom="Service demandes", cas_utilisation=["UC-01"]))
    res = check_rule_5_uc_couvert_par_composant(empty_dossier)
    assert res.passed


def test_rule_6_glossaire_et_synonymes_interdits(empty_dossier: ConceptionDossier):
    empty_dossier.glossaire = GlossaireDocument(
        document=DocumentHeader(type="glossaire"),
        termes=[Terme(terme="dossier", synonymes_interdits=["chemise", "classeur"])],
    )
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        exigences=[Exigence(id="EX-01", enonce="L'agent ouvre une chemise")],
    )
    res = check_rule_6_glossaire_et_synonymes(empty_dossier)
    assert not res.passed
    assert "chemise" in res.violations[0].message


def test_rule_7_risques_responsable_et_mitigation(empty_dossier: ConceptionDossier):
    empty_dossier.risques = RisquesDocument(
        document=DocumentHeader(type="risques"),
        risques=[Risque(id="RSK-01", responsable="", mitigation="")],
    )
    res = check_rule_7_risques_responsable_et_mitigation(empty_dossier)
    assert not res.passed
    assert len(res.violations) == 2

    empty_dossier.risques.risques[0].responsable = "Tech Lead"
    empty_dossier.risques.risques[0].mitigation = "Cluster redondant multi-AZ"
    res = check_rule_7_risques_responsable_et_mitigation(empty_dossier)
    assert res.passed


def test_rule_8_donnees_personnelles(empty_dossier: ConceptionDossier):
    empty_dossier.risques = RisquesDocument(
        document=DocumentHeader(type="risques"),
        donnees_personnelles=[DonneePersonnelle(id="DP-01", finalite="", base_legale="", duree_conservation="")],
    )
    res = check_rule_8_donnees_personnelles_conformite(empty_dossier)
    assert not res.passed
    assert len(res.violations) == 3

    empty_dossier.risques.donnees_personnelles[0].finalite = "Facturation client"
    empty_dossier.risques.donnees_personnelles[0].base_legale = "Obligation légale"
    empty_dossier.risques.donnees_personnelles[0].duree_conservation = "10 ans"
    res = check_rule_8_donnees_personnelles_conformite(empty_dossier)
    assert res.passed


def test_rule_9_plan_cycles(empty_dossier: ConceptionDossier):
    empty_dossier.plan = PlanDocument(
        document=DocumentHeader(type="plan"),
        lots=[
            Lot(id="LOT-01", depend_de=["LOT-02"]),
            Lot(id="LOT-02", depend_de=["LOT-01"]),
        ],
    )
    res = check_rule_9_cycle_dependances_plan(empty_dossier)
    assert not res.passed
    assert "Dépendance circulaire" in res.violations[0].message

    empty_dossier.plan.lots[0].depend_de = []
    res = check_rule_9_cycle_dependances_plan(empty_dossier)
    assert res.passed


def test_rule_10_perimetre_exclu_non_vide(empty_dossier: ConceptionDossier):
    empty_dossier.cadrage = CadrageDocument(
        document=DocumentHeader(type="cadrage"),
        perimetre=Perimetre(inclus=["Module A"], exclu=[""]),
    )
    res = check_rule_10_perimetre_exclu_non_vide(empty_dossier)
    assert not res.passed

    empty_dossier.cadrage.perimetre.exclu = ["Pas de passerelle bancaire en V1"]
    res = check_rule_10_perimetre_exclu_non_vide(empty_dossier)
    assert res.passed


def test_rule_12_integrite_referentielle(empty_dossier: ConceptionDossier):
    # Référence à un objectif fantôme OBJ-99
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        exigences=[Exigence(id="EX-01", objectifs=["OBJ-99"])],
    )
    empty_dossier.cadrage = CadrageDocument(
        document=DocumentHeader(type="cadrage"),
        objectifs=[Objectif(id="OBJ-01", enonce="Objectif réel")],
    )
    res = check_rule_12_integrite_referentielle(empty_dossier)
    assert not res.passed
    assert "OBJ-99" in res.violations[0].message

    empty_dossier.exigences.exigences[0].objectifs = ["OBJ-01"]
    res = check_rule_12_integrite_referentielle(empty_dossier)
    assert res.passed


def test_rule_1_enonce_vide_echoue(empty_dossier: ConceptionDossier):
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        exigences=[Exigence(id="EX-01", enonce="", mesure="réponse < 500 ms au 95e centile")],
    )
    res = check_rule_1_exigences_mesurables(empty_dossier)
    assert not res.passed
    assert "énoncé" in res.violations[0].message


def test_rule_2_test_vide_ne_couvre_pas(empty_dossier: ConceptionDossier):
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        exigences=[Exigence(id="EX-01", enonce="Le système enregistre", mesure="mesure 1")],
    )
    empty_dossier.tests = TestsDocument(
        document=DocumentHeader(type="tests"),
        tests=[TestItem(id="TST-01", exigences=["EX-01"], quand="", alors="")],
    )
    res = check_rule_2_exigence_liee_test(empty_dossier)
    assert not res.passed
    assert "TST-01" in res.violations[0].message


def test_rule_3_uc_sans_nom_ni_scenario_echoue(empty_dossier: ConceptionDossier):
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        cas_utilisation=[
            CasUtilisation(
                id="UC-01",
                nom="",
                acteur_principal="ACT-01",
                exigences=["EX-01"],
                scenario_nominal=["1. ", "2. "],
            )
        ],
    )
    res = check_rule_3_uc_lie_acteur_et_exigence(empty_dossier)
    assert not res.passed
    assert len(res.violations) == 2

    uc = empty_dossier.exigences.cas_utilisation[0]
    uc.nom = "Soumettre une demande"
    uc.scenario_nominal = ["1. L'agent ouvre le formulaire", "2. Le système enregistre"]
    res = check_rule_3_uc_lie_acteur_et_exigence(empty_dossier)
    assert res.passed


def test_rule_5_composant_sans_nom_ne_couvre_pas(empty_dossier: ConceptionDossier):
    empty_dossier.exigences = ExigencesDocument(
        document=DocumentHeader(type="exigences"),
        cas_utilisation=[CasUtilisation(id="UC-01")],
    )
    empty_dossier.architecture = ArchitectureDocument(
        document=DocumentHeader(type="architecture"),
        composants=[Composant(id="CMP-01", nom="", cas_utilisation=["UC-01"])],
    )
    res = check_rule_5_uc_couvert_par_composant(empty_dossier)
    assert not res.passed


def test_rule_6_terme_vide_ou_sans_definition_echoue(empty_dossier: ConceptionDossier):
    empty_dossier.glossaire = GlossaireDocument(
        document=DocumentHeader(type="glossaire"),
        termes=[Terme(terme="", definition="")],
    )
    res = check_rule_6_glossaire_et_synonymes(empty_dossier)
    assert not res.passed

    empty_dossier.glossaire.termes = [Terme(terme="dossier", definition="")]
    res = check_rule_6_glossaire_et_synonymes(empty_dossier)
    assert not res.passed
    assert "définition" in res.violations[0].message

    empty_dossier.glossaire.termes[0].definition = "Ensemble des pièces d'une demande."
    res = check_rule_6_glossaire_et_synonymes(empty_dossier)
    assert res.passed
