"""Modèle de données pour 04-plan.yaml."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .common import DocumentHeader, ConfidenceLevel


class ChargeEstimee(BaseModel):
    model_config = ConfigDict(extra="ignore")
    min: str = ""
    max: str = ""
    confiance: ConfidenceLevel = ConfidenceLevel.MOYENNE


class Lot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    livrable: str = ""
    critere_fin: str = ""
    cas_utilisation: List[str] = Field(default_factory=list)
    depend_de: List[str] = Field(default_factory=list)  # Règle 9 : pas de cycle
    charge_estimee: Optional[ChargeEstimee] = None
    responsable: str = ""


class Jalon(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    lots: List[str] = Field(default_factory=list)
    date_cible: Optional[str] = None
    validation_requise_par: str = ""


class PlanDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document: DocumentHeader
    lots: List[Lot] = Field(default_factory=list)
    jalons: List[Jalon] = Field(default_factory=list)
