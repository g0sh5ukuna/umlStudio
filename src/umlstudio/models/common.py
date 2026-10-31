"""Types et modèles communs pour les dossiers de conception umlStudio."""

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DocumentStatus(StrEnum):
    BROUILLON = "brouillon"
    SOUMIS = "soumis"
    VALIDE = "valide"


class SourceType(StrEnum):
    HUMAIN = "humain"
    DOCUMENT = "document"
    DEDUIT = "deduit"


class Priority(StrEnum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"
    WONT = "wont"


class ItemStatus(StrEnum):
    ACTIF = "actif"
    ABANDONNE = "abandonne"


class DecisionStatus(StrEnum):
    PROPOSEE = "proposee"
    ACCEPTEE = "acceptee"
    REMPLACEE = "remplacee"


class RiskCategory(StrEnum):
    TECHNIQUE = "technique"
    PLANNING = "planning"
    DEPENDANCE = "dependance"
    SECURITE = "securite"
    REGLEMENTAIRE = "reglementaire"
    ORGANISATION = "organisation"


class RiskProbability(StrEnum):
    FAIBLE = "faible"
    MOYENNE = "moyenne"
    HAUTE = "haute"


class RiskImpact(StrEnum):
    FAIBLE = "faible"
    MOYEN = "moyen"
    FORT = "fort"


class RiskStatus(StrEnum):
    OUVERT = "ouvert"
    MAITRISE = "maitrise"
    REALISE = "realise"
    CLOS = "clos"


class ConfidenceLevel(StrEnum):
    FAIBLE = "faible"
    MOYENNE = "moyenne"
    HAUTE = "haute"


class TestLevel(StrEnum):
    UNITAIRE = "unitaire"
    INTEGRATION = "integration"
    CONTRAT_API = "contrat_api"
    SECURITE = "securite"
    PERFORMANCE = "performance"
    RECETTE = "recette"


class TestStatus(StrEnum):
    A_ECRIRE = "a_ecrire"
    ECRIT = "ecrit"
    PASSE = "passe"
    ECHOUE = "echoue"


class LayerType(StrEnum):
    PRESENTATION = "presentation"
    APPLICATION = "application"
    DONNEES = "donnees"
    INFRASTRUCTURE = "infrastructure"


class InterfaceDirection(StrEnum):
    ENTRANT = "entrant"
    SORTANT = "sortant"
    BIDIRECTIONNEL = "bidirectionnel"


class FeasibilityVerdict(StrEnum):
    FAISABLE = "faisable"
    FAISABLE_SOUS_CONDITIONS = "faisable_sous_conditions"
    NON_FAISABLE = "non_faisable"
    A_CONFIRMER = "a_confirmer"


class StakeholderInvolvement(StrEnum):
    VALIDE = "valide"
    CONSULTE = "consulte"
    INFORME = "informe"


class DocumentHeader(BaseModel):
    """En-tête standard présent dans chaque document YAML."""
    model_config = ConfigDict(extra="ignore")

    type: str
    statut: DocumentStatus = DocumentStatus.BROUILLON
    version: str = "0.1.0"
