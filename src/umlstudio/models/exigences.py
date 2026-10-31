"""Modèle de données pour 01-exigences.yaml."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .common import (
    DocumentHeader,
    SourceType,
    Priority,
    ItemStatus,
)


class Acteur(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    type: str = "humain"  # humain | systeme
    description: str = ""
    source: SourceType = SourceType.HUMAIN


class Exigence(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    type: str = "fonctionnelle"  # fonctionnelle | performance | securite | disponibilite | utilisabilite | conformite
    enonce: str = ""
    mesure: str = ""  # Règle 1 : mesure obligatoire
    priorite: Priority = Priority.MUST
    objectifs: List[str] = Field(default_factory=list)
    source: SourceType = SourceType.HUMAIN
    statut: ItemStatus = ItemStatus.ACTIF


class ScenarioAlternatif(BaseModel):
    model_config = ConfigDict(extra="ignore")
    condition: str = ""
    etapes: List[str] = Field(default_factory=list)


class CasUtilisation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    acteur_principal: str = ""  # ACT-xx
    acteurs_secondaires: List[str] = Field(default_factory=list)
    exigences: List[str] = Field(default_factory=list)  # EX-xx
    preconditions: List[str] = Field(default_factory=list)
    scenario_nominal: List[str] = Field(default_factory=list)
    scenarios_alternatifs: List[ScenarioAlternatif] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    endpoints: List[str] = Field(default_factory=list)
    source: SourceType = SourceType.HUMAIN
    statut: ItemStatus = ItemStatus.ACTIF


class ExigencesDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document: DocumentHeader
    acteurs: List[Acteur] = Field(default_factory=list)
    exigences: List[Exigence] = Field(default_factory=list)
    cas_utilisation: List[CasUtilisation] = Field(default_factory=list)
