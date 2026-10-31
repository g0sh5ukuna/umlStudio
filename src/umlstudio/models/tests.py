"""Modèle de données pour 06-tests.yaml."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .common import (
    DocumentHeader,
    TestLevel,
    TestStatus,
)


class Strategie(BaseModel):
    model_config = ConfigDict(extra="ignore")
    niveaux: List[str] = Field(default_factory=lambda: [
        "unitaire", "integration", "contrat_api", "securite", "performance", "recette"
    ])
    environnement_recette: str = ""
    donnees_de_test: str = ""


class TestItem(BaseModel):
    __test__ = False
    model_config = ConfigDict(extra="ignore")
    id: str
    niveau: str = "recette"
    exigences: List[str] = Field(default_factory=list)  # Règle 2
    cas_utilisation: List[str] = Field(default_factory=list)
    etant_donne: str = ""
    quand: str = ""
    alors: str = ""  # résultat attendu, mesurable
    automatise: bool = False
    statut: TestStatus = TestStatus.A_ECRIRE


class TestsDocument(BaseModel):
    __test__ = False
    model_config = ConfigDict(extra="ignore")
    document: DocumentHeader
    strategie: Optional[Strategie] = None
    tests: List[TestItem] = Field(default_factory=list)
    criteres_acceptation_globaux: List[str] = Field(default_factory=list)
