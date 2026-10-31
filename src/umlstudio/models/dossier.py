"""Agrégat représentant un dossier de conception complet avec indexation."""

from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, ConfigDict

from .cadrage import CadrageDocument, Objectif
from .exigences import Acteur, CasUtilisation, Exigence, ExigencesDocument
from .glossaire import GlossaireDocument, Terme
from .architecture import ArchitectureDocument, Composant, Entite
from .plan import Lot, PlanDocument
from .risques import DonneePersonnelle, Risque, RisquesDocument
from .tests import TestItem, TestsDocument
from .validations import ValidationEntry, ValidationsDocument
from .api import Operation


class ConceptionDossier(BaseModel):
    """Représente l'ensemble du dossier de conception logicielle."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    root_path: Path
    cadrage: Optional[CadrageDocument] = None
    exigences: Optional[ExigencesDocument] = None
    glossaire: Optional[GlossaireDocument] = None
    architecture: Optional[ArchitectureDocument] = None
    plan: Optional[PlanDocument] = None
    risques: Optional[RisquesDocument] = None
    tests: Optional[TestsDocument] = None
    validations: Optional[ValidationsDocument] = None
    openapi_endpoints: List[str] = Field(default_factory=list)
    operations: List[Operation] = Field(default_factory=list)
    raw_files: Dict[str, str] = Field(default_factory=dict)  # nom_fichier -> contenu brut

    # Index des identifiants existants : ID -> type/fichier
    def get_id_registry(self) -> Dict[str, str]:
        reg: Dict[str, str] = {}
        if self.cadrage:
            for obj in self.cadrage.objectifs:
                if obj.id:
                    reg[obj.id] = "Objectif (00-cadrage.yaml)"
        if self.exigences:
            for act in self.exigences.acteurs:
                if act.id:
                    reg[act.id] = "Acteur (01-exigences.yaml)"
            for ex in self.exigences.exigences:
                if ex.id:
                    reg[ex.id] = "Exigence (01-exigences.yaml)"
            for uc in self.exigences.cas_utilisation:
                if uc.id:
                    reg[uc.id] = "Cas d'utilisation (01-exigences.yaml)"
        if self.architecture:
            for dec in self.architecture.decisions:
                if dec.id:
                    reg[dec.id] = "Décision (03-architecture.yaml)"
            for cmp in self.architecture.composants:
                if cmp.id:
                    reg[cmp.id] = "Composant (03-architecture.yaml)"
            for ent in self.architecture.entites:
                if ent.id:
                    reg[ent.id] = "Entité (03-architecture.yaml)"
            for ifx in self.architecture.interfaces_externes:
                if ifx.id:
                    reg[ifx.id] = "Interface externe (03-architecture.yaml)"
            if self.architecture.deploiement:
                for nod in self.architecture.deploiement.noeuds:
                    if nod.id:
                        reg[nod.id] = "Nœud de déploiement (03-architecture.yaml)"
        if self.plan:
            for lot in self.plan.lots:
                if lot.id:
                    reg[lot.id] = "Lot (04-plan.yaml)"
            for jal in self.plan.jalons:
                if jal.id:
                    reg[jal.id] = "Jalon (04-plan.yaml)"
        if self.risques:
            for rsk in self.risques.risques:
                if rsk.id:
                    reg[rsk.id] = "Risque (05-risques.yaml)"
            for dp in self.risques.donnees_personnelles:
                if dp.id:
                    reg[dp.id] = "Donnée personnelle (05-risques.yaml)"
        if self.tests:
            for tst in self.tests.tests:
                if tst.id:
                    reg[tst.id] = "Test (06-tests.yaml)"
        return reg

    def get_exigences_actifs(self) -> List[Exigence]:
        if not self.exigences:
            return []
        return [ex for ex in self.exigences.exigences if ex.statut != "abandonne"]

    def get_cas_utilisation_actifs(self) -> List[CasUtilisation]:
        if not self.exigences:
            return []
        return [uc for uc in self.exigences.cas_utilisation if uc.statut != "abandonne"]
