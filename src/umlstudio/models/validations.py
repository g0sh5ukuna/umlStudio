"""Modèle de données pour validations.yaml."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Validateur(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nom: str = ""
    role: str = ""


class ValidationEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document: str  # ex: 00-cadrage.yaml
    version: str = "0.1.0"
    sha256: str = ""
    commit: str = ""
    validateur: Optional[Validateur] = None
    date: str = ""  # AAAA-MM-JJ
    preuve: str = ""  # URL de PR / MR
    reserves: List[str] = Field(default_factory=list)


class ValidationsDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    validations: List[ValidationEntry] = Field(default_factory=list)
