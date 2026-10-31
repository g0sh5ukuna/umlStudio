"""Modèle de données pour 00-cadrage.yaml."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .common import (
    DocumentHeader,
    SourceType,
    FeasibilityVerdict,
    StakeholderInvolvement,
)


class ProjectPerson(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nom: str = ""
    role: str = ""


class ProjectInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nom: str = ""
    code: str = ""
    commanditaire: Optional[ProjectPerson] = None
    responsable_projet: Optional[ProjectPerson] = None


class Objectif(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    enonce: str = ""
    indicateur: str = ""
    valeur_actuelle: str = ""
    cible: str = ""
    source: SourceType = SourceType.HUMAIN


class Perimetre(BaseModel):
    model_config = ConfigDict(extra="ignore")
    inclus: List[str] = Field(default_factory=list)
    exclu: List[str] = Field(default_factory=list)


class Contrainte(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str = "technique"
    enonce: str = ""
    source: SourceType = SourceType.HUMAIN


class PartiePrenante(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nom: str = ""
    role: str = ""
    implication: StakeholderInvolvement = StakeholderInvolvement.VALIDE


class Faisabilite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    verdict: FeasibilityVerdict = FeasibilityVerdict.A_CONFIRMER
    conditions: List[str] = Field(default_factory=list)
    hypotheses: List[str] = Field(default_factory=list)


class NonTrouve(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question: str = ""
    a_qui_demander: str = ""


class CadrageDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document: DocumentHeader
    projet: Optional[ProjectInfo] = None
    contexte: str = ""
    objectifs: List[Objectif] = Field(default_factory=list)
    perimetre: Optional[Perimetre] = None
    contraintes: List[Contrainte] = Field(default_factory=list)
    parties_prenantes: List[PartiePrenante] = Field(default_factory=list)
    faisabilite: Optional[Faisabilite] = None
    non_trouve: List[NonTrouve] = Field(default_factory=list)
