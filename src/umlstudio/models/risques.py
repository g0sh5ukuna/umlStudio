"""Modèle de données pour 05-risques.yaml."""

from typing import List
from pydantic import BaseModel, Field, ConfigDict
from .common import (
    DocumentHeader,
    RiskCategory,
    RiskProbability,
    RiskImpact,
    RiskStatus,
)


class Risque(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    categorie: RiskCategory = RiskCategory.TECHNIQUE
    enonce: str = ""
    probabilite: RiskProbability = RiskProbability.MOYENNE
    impact: RiskImpact = RiskImpact.MOYEN
    mitigation: str = ""  # Règle 7 : mitigation obligatoire
    declencheur: str = ""
    responsable: str = ""  # Règle 7 : responsable obligatoire
    statut: RiskStatus = RiskStatus.OUVERT


class DonneePersonnelle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    entite: str = ""  # ENT-xx
    champs: List[str] = Field(default_factory=list)
    finalite: str = ""  # Règle 8
    base_legale: str = ""  # Règle 8
    duree_conservation: str = ""  # Règle 8
    destinataires: List[str] = Field(default_factory=list)
    transfert_hors_pays: bool = False


class RisquesDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document: DocumentHeader
    risques: List[Risque] = Field(default_factory=list)
    donnees_personnelles: List[DonneePersonnelle] = Field(default_factory=list)
