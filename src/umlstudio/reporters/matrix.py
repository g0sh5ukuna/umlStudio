"""Calcul et génération de la matrice de traçabilité de bout en bout."""

from typing import Any, Dict, List, Set
from pydantic import BaseModel, Field

from ..models.dossier import ConceptionDossier


class TraceabilityRow(BaseModel):
    objectif_id: str = "-"
    exigence_id: str = "-"
    exigence_titre: str = ""
    exigence_priorite: str = "-"
    cas_utilisation_id: str = "-"
    cas_utilisation_nom: str = ""
    composants_ids: List[str] = Field(default_factory=list)
    tests_ids: List[str] = Field(default_factory=list)
    tests_statuts: List[str] = Field(default_factory=list)


class TraceabilityReport(BaseModel):
    rows: List[TraceabilityRow] = Field(default_factory=list)
    total_exigences: int = 0
    tested_exigences: int = 0
    coverage_tests_pct: float = 0.0
    total_ucs: int = 0
    covered_ucs: int = 0
    coverage_ucs_pct: float = 0.0


def build_traceability_matrix(dossier: ConceptionDossier) -> TraceabilityReport:
    """Construit la matrice croisée complète Objectif -> Exigence -> Cas d'utilisation -> Composant -> Test."""
    report = TraceabilityReport()

    exigences = dossier.get_exigences_actifs()
    ucs = dossier.get_cas_utilisation_actifs()
    report.total_exigences = len(exigences)
    report.total_ucs = len(ucs)

    # Indexation des tests par exigence et par UC
    tests_by_ex: Dict[str, List[str]] = {}
    tests_status_by_ex: Dict[str, List[str]] = {}
    if dossier.tests:
        for tst in dossier.tests.tests:
            for ex_id in tst.exigences:
                tests_by_ex.setdefault(ex_id, []).append(tst.id)
                tests_status_by_ex.setdefault(ex_id, []).append(str(tst.statut))

    # Indexation des composants par UC
    cmp_by_uc: Dict[str, List[str]] = {}
    if dossier.architecture:
        for cmp in dossier.architecture.composants:
            for uc_id in cmp.cas_utilisation:
                cmp_by_uc.setdefault(uc_id, []).append(cmp.id)

    # Indexation des UCs par exigence
    ucs_by_ex: Dict[str, List[Any]] = {}
    for uc in ucs:
        for ex_id in uc.exigences:
            ucs_by_ex.setdefault(ex_id, []).append(uc)

    # Compteurs de couverture
    tested_ex_set: Set[str] = set()
    covered_uc_set: Set[str] = set()

    for ex in exigences:
        linked_tests = tests_by_ex.get(ex.id, [])
        linked_statuses = tests_status_by_ex.get(ex.id, [])
        if linked_tests:
            tested_ex_set.add(ex.id)

        linked_ucs = ucs_by_ex.get(ex.id, [])
        obj_id = ex.objectifs[0] if ex.objectifs else "-"

        if linked_ucs:
            for uc in linked_ucs:
                cmps = cmp_by_uc.get(uc.id, [])
                if cmps:
                    covered_uc_set.add(uc.id)

                report.rows.append(
                    TraceabilityRow(
                        objectif_id=obj_id,
                        exigence_id=ex.id,
                        exigence_titre=ex.enonce,
                        exigence_priorite=str(ex.priorite),
                        cas_utilisation_id=uc.id,
                        cas_utilisation_nom=uc.nom,
                        composants_ids=cmps,
                        tests_ids=linked_tests,
                        tests_statuts=linked_statuses,
                    )
                )
        else:
            report.rows.append(
                TraceabilityRow(
                    objectif_id=obj_id,
                    exigence_id=ex.id,
                    exigence_titre=ex.enonce,
                    exigence_priorite=str(ex.priorite),
                    cas_utilisation_id="-",
                    cas_utilisation_nom="(aucun)",
                    composants_ids=[],
                    tests_ids=linked_tests,
                    tests_statuts=linked_statuses,
                )
            )

    report.tested_exigences = len(tested_ex_set)
    report.coverage_tests_pct = (
        round((report.tested_exigences / report.total_exigences) * 100, 1)
        if report.total_exigences > 0
        else 100.0
    )

    report.covered_ucs = len(covered_uc_set)
    report.coverage_ucs_pct = (
        round((report.covered_ucs / report.total_ucs) * 100, 1)
        if report.total_ucs > 0
        else 100.0
    )

    return report
