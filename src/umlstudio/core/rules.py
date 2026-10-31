"""Moteur d'évaluation des 12 contrôles : 10 règles fondamentales et 2 contrôles d'intégrité."""

import re
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from ..models.dossier import ConceptionDossier
from .graph import DependencyGraph
from .integrity import audit_validations, compute_sha256


class RuleViolation(BaseModel):
    item_id: Optional[str] = None
    file_name: str
    message: str
    recommendation: Optional[str] = None


class RuleResult(BaseModel):
    rule_number: int
    rule_id: str
    title: str
    passed: bool
    severity: str = "ERROR"  # ERROR | WARNING | INFO
    summary: str
    violations: List[RuleViolation] = Field(default_factory=list)


def _is_blank(text: str) -> bool:
    return not text or not text.strip()


def _is_blank_step(step: str) -> bool:
    """Une étape de scénario réduite à sa numérotation ("1. ") est vide."""
    return not re.sub(r"^\s*\d+[.)]?\s*", "", step or "").strip()


def check_rule_1_exigences_mesurables(dossier: ConceptionDossier) -> RuleResult:
    """Règle 1 : Toute exigence a une mesure vérifiable."""
    violations: List[RuleViolation] = []
    if not dossier.exigences:
        return RuleResult(
            rule_number=1,
            rule_id="REGLE-01",
            title="Mesure vérifiable sur chaque exigence",
            passed=False,
            summary="Le document 01-exigences.yaml est absent ou invalide.",
            violations=[RuleViolation(file_name="01-exigences.yaml", message="Document manquant")],
        )

    invalid_mesures = {"", "à définir", "a definir", "todo", "tbd", "n/a", "none", "inconnu"}
    for ex in dossier.get_exigences_actifs():
        if _is_blank(ex.enonce):
            violations.append(
                RuleViolation(
                    item_id=ex.id,
                    file_name="01-exigences.yaml",
                    message=f"L'exigence {ex.id} n'a pas d'énoncé.",
                    recommendation="Formuler l'exigence en une phrase : 'Le système doit...'.",
                )
            )
        mesure_clean = ex.mesure.strip().lower()
        if not mesure_clean or mesure_clean in invalid_mesures or len(mesure_clean) < 5:
            violations.append(
                RuleViolation(
                    item_id=ex.id,
                    file_name="01-exigences.yaml",
                    message=f"L'exigence {ex.id} n'a pas de mesure vérifiable (actuelle: '{ex.mesure}').",
                    recommendation="Indiquer une métrique chiffrée ou un critère binaire testable (ex: 'temps de réponse < 200ms au 95e centile').",
                )
            )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=1,
        rule_id="REGLE-01",
        title="Mesure vérifiable sur chaque exigence",
        passed=passed,
        summary="Toutes les exigences actives ont un énoncé et une mesure vérifiable." if passed else f"{len(violations)} anomalie(s) d'énoncé ou de mesure.",
        violations=violations,
    )


def check_rule_2_exigence_liee_test(dossier: ConceptionDossier) -> RuleResult:
    """Règle 2 : Toute exigence est liée à au moins un test."""
    violations: List[RuleViolation] = []
    if not dossier.exigences or not dossier.tests:
        return RuleResult(
            rule_number=2,
            rule_id="REGLE-02",
            title="Couverture des exigences par les tests",
            passed=False,
            summary="01-exigences.yaml ou 06-tests.yaml est manquant.",
            violations=[RuleViolation(file_name="06-tests.yaml", message="Document manquant")],
        )

    # Un test sans action ni résultat attendu ne couvre rien.
    tested_ex_ids: Set[str] = set()
    empty_tests: Dict[str, List[str]] = {}
    for tst in dossier.tests.tests:
        for ex_id in tst.exigences:
            if _is_blank(tst.quand) or _is_blank(tst.alors):
                empty_tests.setdefault(ex_id, []).append(tst.id)
            else:
                tested_ex_ids.add(ex_id)

    for ex in dossier.get_exigences_actifs():
        if ex.id not in tested_ex_ids and ex.id in empty_tests:
            violations.append(
                RuleViolation(
                    item_id=ex.id,
                    file_name="06-tests.yaml",
                    message=f"L'exigence {ex.id} n'est liée qu'à des tests vides ({', '.join(empty_tests[ex.id])}).",
                    recommendation="Renseigner 'quand' et 'alors' (résultat attendu, mesurable) dans ces tests.",
                )
            )
        elif ex.id not in tested_ex_ids:
            violations.append(
                RuleViolation(
                    item_id=ex.id,
                    file_name="01-exigences.yaml",
                    message=f"L'exigence {ex.id} ('{ex.enonce[:40]}...') n'est couverte par aucun test dans 06-tests.yaml.",
                    recommendation=f"Ajouter au moins un test dans 06-tests.yaml avec 'exigences: [{ex.id}]'.",
                )
            )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=2,
        rule_id="REGLE-02",
        title="Couverture des exigences par les tests",
        passed=passed,
        summary="100 % des exigences actives sont couvertes par au moins un test." if passed else f"{len(violations)} exigence(s) non testée(s).",
        violations=violations,
    )


def check_rule_3_uc_lie_acteur_et_exigence(dossier: ConceptionDossier) -> RuleResult:
    """Règle 3 : Tout cas d'utilisation est lié à au moins une exigence et un acteur."""
    violations: List[RuleViolation] = []
    if not dossier.exigences:
        return RuleResult(
            rule_number=3,
            rule_id="REGLE-03",
            title="Liaison des cas d'utilisation (Acteur + Exigence)",
            passed=False,
            summary="01-exigences.yaml manquant.",
            violations=[],
        )

    for uc in dossier.get_cas_utilisation_actifs():
        if _is_blank(uc.nom):
            violations.append(
                RuleViolation(
                    item_id=uc.id,
                    file_name="01-exigences.yaml",
                    message=f"Le cas d'utilisation {uc.id} n'a pas de nom.",
                    recommendation="Nommer le cas d'utilisation par un verbe et un complément : 'Soumettre une demande'.",
                )
            )
        if all(_is_blank_step(step) for step in uc.scenario_nominal):
            violations.append(
                RuleViolation(
                    item_id=uc.id,
                    file_name="01-exigences.yaml",
                    message=f"Le cas d'utilisation {uc.id} n'a pas de scénario nominal.",
                    recommendation="Décrire les étapes du scénario nominal, une action par ligne.",
                )
            )
        if not uc.acteur_principal or not uc.acteur_principal.strip():
            violations.append(
                RuleViolation(
                    item_id=uc.id,
                    file_name="01-exigences.yaml",
                    message=f"Le cas d'utilisation {uc.id} n'a pas d'acteur principal.",
                    recommendation="Renseigner 'acteur_principal: ACT-xx'.",
                )
            )
        if not uc.exigences or len([e for e in uc.exigences if e.strip()]) == 0:
            violations.append(
                RuleViolation(
                    item_id=uc.id,
                    file_name="01-exigences.yaml",
                    message=f"Le cas d'utilisation {uc.id} n'est rattaché à aucune exigence.",
                    recommendation="Renseigner au moins une exigence 'exigences: [EX-xx]'.",
                )
            )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=3,
        rule_id="REGLE-03",
        title="Liaison des cas d'utilisation (Acteur + Exigence)",
        passed=passed,
        summary="Tous les cas d'utilisation sont nommés, décrits, liés à un acteur et à au moins une exigence." if passed else f"{len(violations)} anomalie(s) sur les cas d'utilisation.",
        violations=violations,
    )


def check_rule_4_openapi_endpoints_lies_uc(dossier: ConceptionDossier) -> RuleResult:
    """Règle 4 : Tout endpoint OpenAPI est lié à au moins un cas d'utilisation."""
    violations: List[RuleViolation] = []
    if not dossier.openapi_endpoints:
        # Aucun fichier openapi trouvé dans api/ : on vérifie si des endpoints sont déclarés dans les UCs
        return RuleResult(
            rule_number=4,
            rule_id="REGLE-04",
            title="Liaison des endpoints OpenAPI aux cas d'utilisation",
            passed=True,
            severity="INFO",
            summary="Aucun contrat OpenAPI trouvé dans api/ (contrôle ignoré ou en attente d'écriture).",
            violations=[],
        )

    used_endpoints: Set[str] = set()
    if dossier.exigences:
        for uc in dossier.get_cas_utilisation_actifs():
            for ep in uc.endpoints:
                used_endpoints.add(ep.strip())

    for op_id in dossier.openapi_endpoints:
        if op_id not in used_endpoints:
            violations.append(
                RuleViolation(
                    item_id=op_id,
                    file_name="api/openapi.yaml",
                    message=f"L'endpoint OpenAPI '{op_id}' n'est associé à aucun cas d'utilisation.",
                    recommendation=f"Ajouter '{op_id}' dans la liste 'endpoints' du cas d'utilisation correspondant dans 01-exigences.yaml.",
                )
            )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=4,
        rule_id="REGLE-04",
        title="Liaison des endpoints OpenAPI aux cas d'utilisation",
        passed=passed,
        summary="Tous les endpoints OpenAPI sont liés à un cas d'utilisation." if passed else f"{len(violations)} endpoint(s) orphelin(s).",
        violations=violations,
    )


def check_rule_5_uc_couvert_par_composant(dossier: ConceptionDossier) -> RuleResult:
    """Règle 5 : Tout cas d'utilisation est couvert par au moins un composant."""
    violations: List[RuleViolation] = []
    if not dossier.exigences or not dossier.architecture:
        return RuleResult(
            rule_number=5,
            rule_id="REGLE-05",
            title="Couverture des cas d'utilisation par les composants",
            passed=False,
            summary="01-exigences.yaml ou 03-architecture.yaml manquant.",
            violations=[],
        )

    # Un composant sans nom n'est qu'un emplacement du modèle : il ne couvre rien.
    covered_ucs: Set[str] = set()
    for cmp in dossier.architecture.composants:
        if _is_blank(cmp.nom):
            continue
        for uc_id in cmp.cas_utilisation:
            covered_ucs.add(uc_id.strip())

    for uc in dossier.get_cas_utilisation_actifs():
        if uc.id not in covered_ucs:
            violations.append(
                RuleViolation(
                    item_id=uc.id,
                    file_name="01-exigences.yaml",
                    message=f"Le cas d'utilisation {uc.id} n'est pris en charge par aucun composant dans 03-architecture.yaml.",
                    recommendation=f"Associer {uc.id} à un composant applicatif ou de présentation (cas_utilisation: [{uc.id}]).",
                )
            )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=5,
        rule_id="REGLE-05",
        title="Couverture des cas d'utilisation par les composants",
        passed=passed,
        summary="Tous les cas d'utilisation sont couverts par l'architecture logicielle." if passed else f"{len(violations)} cas d'utilisation sans composant associé.",
        violations=violations,
    )


def check_rule_6_glossaire_et_synonymes(dossier: ConceptionDossier) -> RuleResult:
    """Règle 6 : Termes métier définis dans le glossaire + interdiction des synonymes interdits."""
    violations: List[RuleViolation] = []
    termes = [t for t in dossier.glossaire.termes if not _is_blank(t.terme)] if dossier.glossaire else []
    if not termes:
        violations.append(
            RuleViolation(
                file_name="02-glossaire.yaml",
                message="Le glossaire métier est vide ou absent.",
                recommendation="Définir les termes métier essentiels du domaine pour lever toute ambiguïté.",
            )
        )
        return RuleResult(
            rule_number=6,
            rule_id="REGLE-06",
            title="Conformité au glossaire et vocabulaire métier",
            passed=False,
            severity="WARNING",
            summary="Glossaire vide ou non renseigné.",
            violations=violations,
        )

    # Vérification des synonymes interdits employés dans les exigences
    forbidden_map: Dict[str, str] = {}
    for item in termes:
        for syn in item.synonymes_interdits:
            if syn.strip():
                forbidden_map[syn.strip().lower()] = item.terme

    if dossier.exigences:
        for ex in dossier.get_exigences_actifs():
            text = f"{ex.enonce} {ex.mesure}".lower()
            for syn, canon in forbidden_map.items():
                pattern = r"\b" + re.escape(syn) + r"\b"
                if re.search(pattern, text):
                    violations.append(
                        RuleViolation(
                            item_id=ex.id,
                            file_name="01-exigences.yaml",
                            message=f"L'exigence {ex.id} emploie le synonyme interdit '{syn}' au lieu de '{canon}'.",
                            recommendation=f"Remplacer '{syn}' par le terme canonique du glossaire '{canon}'.",
                        )
                    )

    for item in termes:
        if _is_blank(item.definition):
            violations.append(
                RuleViolation(
                    item_id=item.terme,
                    file_name="02-glossaire.yaml",
                    message=f"Le terme '{item.terme}' n'a pas de définition.",
                    recommendation="Définir le terme en une phrase, sans employer de synonyme interdit.",
                )
            )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=6,
        rule_id="REGLE-06",
        title="Conformité au glossaire et vocabulaire métier",
        passed=passed,
        severity="WARNING" if not passed else "INFO",
        summary="Vocabulaire conforme au glossaire." if passed else f"{len(violations)} non-conformité(s) de vocabulaire détectée(s).",
        violations=violations,
    )


def check_rule_7_risques_responsable_et_mitigation(dossier: ConceptionDossier) -> RuleResult:
    """Règle 7 : Tout risque a un responsable et une mitigation."""
    violations: List[RuleViolation] = []
    if not dossier.risques:
        return RuleResult(
            rule_number=7,
            rule_id="REGLE-07",
            title="Mitigation et gouvernance des risques",
            passed=False,
            summary="05-risques.yaml manquant.",
            violations=[],
        )

    for rsk in dossier.risques.risques:
        if rsk.statut != "clos":
            if not rsk.responsable or not rsk.responsable.strip():
                violations.append(
                    RuleViolation(
                        item_id=rsk.id,
                        file_name="05-risques.yaml",
                        message=f"Le risque {rsk.id} n'a pas de responsable désigné.",
                        recommendation="Assigner une personne ou un rôle responsable du suivi de ce risque.",
                    )
                )
            if not rsk.mitigation or not rsk.mitigation.strip():
                violations.append(
                    RuleViolation(
                        item_id=rsk.id,
                        file_name="05-risques.yaml",
                        message=f"Le risque {rsk.id} n'a pas de plan de mitigation.",
                        recommendation="Décrire le plan d'action préventif ou curatif pour mitiger le risque.",
                    )
                )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=7,
        rule_id="REGLE-07",
        title="Mitigation et gouvernance des risques",
        passed=passed,
        summary="Tous les risques ouverts ont un responsable et une mitigation." if passed else f"{len(violations)} risque(s) sans responsable ou sans mitigation.",
        violations=violations,
    )


def check_rule_8_donnees_personnelles_conformite(dossier: ConceptionDossier) -> RuleResult:
    """Règle 8 : Toute donnée personnelle a une finalité, une base légale et une durée de conservation."""
    violations: List[RuleViolation] = []
    if not dossier.risques:
        return RuleResult(
            rule_number=8,
            rule_id="REGLE-08",
            title="Conformité des données personnelles (RGPD / APDP)",
            passed=False,
            summary="05-risques.yaml manquant.",
            violations=[],
        )

    declared_dp_entities: Set[str] = set()
    for dp in dossier.risques.donnees_personnelles:
        if dp.entite:
            declared_dp_entities.add(dp.entite)
        if not dp.finalite or not dp.finalite.strip():
            violations.append(
                RuleViolation(
                    item_id=dp.id,
                    file_name="05-risques.yaml",
                    message=f"La fiche {dp.id} n'a pas de finalité définie.",
                    recommendation="Spécifier précisément l'objectif du traitement de la donnée.",
                )
            )
        if not dp.base_legale or not dp.base_legale.strip():
            violations.append(
                RuleViolation(
                    item_id=dp.id,
                    file_name="05-risques.yaml",
                    message=f"La fiche {dp.id} n'a pas de base légale déclarée.",
                    recommendation="Renseigner la base légale (consentement, exécution d'un contrat, obligation légale, intérêt légitime).",
                )
            )
        if not dp.duree_conservation or not dp.duree_conservation.strip():
            violations.append(
                RuleViolation(
                    item_id=dp.id,
                    file_name="05-risques.yaml",
                    message=f"La fiche {dp.id} n'a pas de durée de conservation fixée.",
                    recommendation="Définir la durée de conservation (ex: 'durée du compte + 3 ans').",
                )
            )

    # Cross-check avec les entités d'architecture
    if dossier.architecture:
        for ent in dossier.architecture.entites:
            for attr in ent.attributs:
                if attr.donnee_personnelle and ent.id not in declared_dp_entities:
                    violations.append(
                        RuleViolation(
                            item_id=ent.id,
                            file_name="03-architecture.yaml",
                            message=f"L'attribut '{attr.nom}' de l'entité {ent.id} est marqué comme donnée personnelle mais {ent.id} n'apparaît pas dans 05-risques.yaml.",
                            recommendation=f"Ajouter une déclaration 'donnees_personnelles' pour {ent.id} dans 05-risques.yaml.",
                        )
                    )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=8,
        rule_id="REGLE-08",
        title="Conformité des données personnelles (RGPD / APDP)",
        passed=passed,
        summary="Toutes les données personnelles ont une finalité, une base légale et une durée de conservation." if passed else f"{len(violations)} non-conformité(s) de données personnelles.",
        violations=violations,
    )


def check_rule_9_cycle_dependances_plan(dossier: ConceptionDossier) -> RuleResult:
    """Règle 9 : Le graphe des dépendances du plan ne contient pas de cycle."""
    violations: List[RuleViolation] = []
    if not dossier.plan or not dossier.plan.lots:
        return RuleResult(
            rule_number=9,
            rule_id="REGLE-09",
            title="Acyclicité du plan de lotissement (DAG)",
            passed=True,
            summary="Aucun lot défini ou plan vide.",
            violations=[],
        )

    graph = DependencyGraph(dossier.plan.lots)
    cycle = graph.detect_cycles()

    if cycle:
        cycle_str = " -> ".join(cycle)
        violations.append(
            RuleViolation(
                file_name="04-plan.yaml",
                message=f"Dépendance circulaire détectée entre lots : {cycle_str}",
                recommendation="Rompre la boucle de dépendance en réordonnant les livrables des lots.",
            )
        )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=9,
        rule_id="REGLE-09",
        title="Acyclicité du plan de lotissement (DAG)",
        passed=passed,
        summary="Le plan forme un graphe orienté acyclique valide (aucun cycle)." if passed else "Cycle de dépendances détecté dans le plan !",
        violations=violations,
    )


def check_rule_10_perimetre_exclu_non_vide(dossier: ConceptionDossier) -> RuleResult:
    """Règle 10 : Le périmètre exclu n'est pas vide."""
    violations: List[RuleViolation] = []
    if not dossier.cadrage or not dossier.cadrage.perimetre:
        return RuleResult(
            rule_number=10,
            rule_id="REGLE-10",
            title="Délimitation stricte du périmètre exclu",
            passed=False,
            summary="00-cadrage.yaml sans section périmètre.",
            violations=[RuleViolation(file_name="00-cadrage.yaml", message="Périmètre non spécifié")],
        )

    exclus = [e.strip() for e in dossier.cadrage.perimetre.exclu if e and e.strip()]
    if not exclus:
        violations.append(
            RuleViolation(
                file_name="00-cadrage.yaml",
                message="La liste du périmètre exclu est vide ou ne contient que des chaînes vides.",
                recommendation="Expliciter ce qui N'EST PAS dans le projet pour éviter tout effet de glissement de périmètre.",
            )
        )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=10,
        rule_id="REGLE-10",
        title="Délimitation stricte du périmètre exclu",
        passed=passed,
        summary="Le périmètre exclu est clairement délimité." if passed else "Périmètre exclu vide.",
        violations=violations,
    )


def check_rule_11_integrite_validations(dossier: ConceptionDossier) -> RuleResult:
    """Règle 11 : Intégrité cryptographique SHA-256 et statut des validations."""
    violations: List[RuleViolation] = []
    anomalies = audit_validations(dossier.root_path, dossier.validations)

    for anom in anomalies:
        violations.append(
            RuleViolation(
                file_name=anom.get("document", "validations.yaml"),
                message=anom["message"],
                recommendation="Mettre à jour le hash dans validations.yaml via 'umlstudio sign' après approbation de la PR.",
            )
        )

    # Vérifier si un document a statut: valide mais n'a pas de validation enregistrée
    docs = [
        ("00-cadrage.yaml", dossier.cadrage),
        ("01-exigences.yaml", dossier.exigences),
        ("02-glossaire.yaml", dossier.glossaire),
        ("03-architecture.yaml", dossier.architecture),
        ("04-plan.yaml", dossier.plan),
        ("05-risques.yaml", dossier.risques),
        ("06-tests.yaml", dossier.tests),
    ]

    signed_docs = set()
    if dossier.validations:
        for v in dossier.validations.validations:
            if v.sha256:
                signed_docs.add(v.document)

    for doc_name, doc_obj in docs:
        if doc_obj and getattr(doc_obj, "document", None):
            if doc_obj.document.statut == "valide" and doc_name not in signed_docs:
                violations.append(
                    RuleViolation(
                        file_name=doc_name,
                        message=f"Le document '{doc_name}' est marqué au statut 'valide' mais n'a pas de signature SHA-256 dans validations.yaml.",
                        recommendation=f"Exécuter 'umlstudio sign {doc_name}' ou repasser le document en 'statut: soumis'.",
                    )
                )

    passed = len(violations) == 0
    return RuleResult(
        rule_number=11,
        rule_id="REGLE-11",
        title="Intégrité SHA-256 et registre des validations",
        passed=passed,
        summary="Toutes les validations enregistrées correspondent aux empreintes réelles." if passed else f"{len(violations)} anomalie(s) d'intégrité de validation.",
        violations=violations,
    )


def check_rule_12_integrite_referentielle(dossier: ConceptionDossier) -> RuleResult:
    """Règle 12 : Intégrité référentielle croisée entre tous les identifiants (pas de liens orphelins)."""
    violations: List[RuleViolation] = []
    reg = dossier.get_id_registry()

    def check_ref(ref_id: str, source_file: str, item_id: str, field_desc: str):
        if not ref_id or not ref_id.strip():
            return
        clean_id = ref_id.strip()
        if clean_id not in reg:
            violations.append(
                RuleViolation(
                    item_id=item_id,
                    file_name=source_file,
                    message=f"L'élément {item_id} référence l'identifiant inconnu '{clean_id}' ({field_desc}).",
                    recommendation=f"Vérifier que '{clean_id}' est bien déclaré ou corriger la référence.",
                )
            )

    # Exigences -> Objectifs
    if dossier.exigences:
        for ex in dossier.exigences.exigences:
            for obj_id in ex.objectifs:
                check_ref(obj_id, "01-exigences.yaml", ex.id, "objectif")

        # Cas d'utilisation -> Acteurs & Exigences
        for uc in dossier.exigences.cas_utilisation:
            if uc.acteur_principal:
                check_ref(uc.acteur_principal, "01-exigences.yaml", uc.id, "acteur principal")
            for act_sec in uc.acteurs_secondaires:
                check_ref(act_sec, "01-exigences.yaml", uc.id, "acteur secondaire")
            for ex_id in uc.exigences:
                check_ref(ex_id, "01-exigences.yaml", uc.id, "exigence liée")

    # Composants -> Cas d'utilisation & Composants dépendants
    if dossier.architecture:
        for cmp in dossier.architecture.composants:
            for uc_id in cmp.cas_utilisation:
                check_ref(uc_id, "03-architecture.yaml", cmp.id, "cas d'utilisation")
            for dep in cmp.depend_de:
                check_ref(dep, "03-architecture.yaml", cmp.id, "composant dépendant")

    # Plan -> Cas d'utilisation & Lots dépendants
    if dossier.plan:
        for lot in dossier.plan.lots:
            for uc_id in lot.cas_utilisation:
                check_ref(uc_id, "04-plan.yaml", lot.id, "cas d'utilisation")
            for dep in lot.depend_de:
                check_ref(dep, "04-plan.yaml", lot.id, "lot dépendant")
        for jal in dossier.plan.jalons:
            for lot_id in jal.lots:
                check_ref(lot_id, "04-plan.yaml", jal.id, "lot du jalon")

    # Schéma : clés étrangères -> Entités
    if dossier.architecture:
        for ent in dossier.architecture.entites:
            for attr in ent.attributs:
                if attr.reference:
                    check_ref(attr.reference, "03-architecture.yaml", ent.id, f"clé étrangère {attr.nom}")

    # Contrat d'API : effets en base -> Entités
    for op in dossier.operations:
        for effet in op.effets:
            check_ref(effet.entite, "api/openapi.yaml", op.operation_id, f"effet en base ({effet.action})")

    # Risques DP -> Entités
    if dossier.risques:
        for dp in dossier.risques.donnees_personnelles:
            if dp.entite:
                check_ref(dp.entite, "05-risques.yaml", dp.id, "entité de données")

    # Tests -> Exigences & Cas d'utilisation
    if dossier.tests:
        for tst in dossier.tests.tests:
            for ex_id in tst.exigences:
                check_ref(ex_id, "06-tests.yaml", tst.id, "exigence testée")
            for uc_id in tst.cas_utilisation:
                check_ref(uc_id, "06-tests.yaml", tst.id, "cas d'utilisation testé")

    passed = len(violations) == 0
    return RuleResult(
        rule_number=12,
        rule_id="REGLE-12",
        title="Intégrité référentielle croisée (zéro identifiant orphelin)",
        passed=passed,
        summary="Tous les identifiants référencés sont valides et déclarés." if passed else f"{len(violations)} référence(s) orpheline(s) détectée(s).",
        violations=violations,
    )


def evaluate_all_rules(dossier: ConceptionDossier) -> List[RuleResult]:
    """Exécute l'ensemble des règles de contrôle sur le dossier."""
    return [
        check_rule_1_exigences_mesurables(dossier),
        check_rule_2_exigence_liee_test(dossier),
        check_rule_3_uc_lie_acteur_et_exigence(dossier),
        check_rule_4_openapi_endpoints_lies_uc(dossier),
        check_rule_5_uc_couvert_par_composant(dossier),
        check_rule_6_glossaire_et_synonymes(dossier),
        check_rule_7_risques_responsable_et_mitigation(dossier),
        check_rule_8_donnees_personnelles_conformite(dossier),
        check_rule_9_cycle_dependances_plan(dossier),
        check_rule_10_perimetre_exclu_non_vide(dossier),
        check_rule_11_integrite_validations(dossier),
        check_rule_12_integrite_referentielle(dossier),
    ]
