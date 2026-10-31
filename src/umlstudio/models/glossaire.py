"""Modèle de données pour 02-glossaire.yaml."""

from typing import List
from pydantic import BaseModel, Field, ConfigDict
from .common import DocumentHeader, SourceType


class Terme(BaseModel):
    model_config = ConfigDict(extra="ignore")
    terme: str
    definition: str = ""
    synonymes_interdits: List[str] = Field(default_factory=list)
    exemple: str = ""
    source: SourceType = SourceType.HUMAIN


class GlossaireDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document: DocumentHeader
    termes: List[Terme] = Field(default_factory=list)
