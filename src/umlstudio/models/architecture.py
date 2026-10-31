"""Modèle de données pour 03-architecture.yaml."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .common import (
    DocumentHeader,
    SourceType,
    DecisionStatus,
    LayerType,
    InterfaceDirection,
)


class Decision(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    sujet: str = ""
    choix: str = ""
    pourquoi: str = ""
    risque_principal: str = ""
    alternative_ecartee: str = ""
    statut: DecisionStatus = DecisionStatus.PROPOSEE


class Composant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    couche: LayerType = LayerType.APPLICATION
    responsabilite: str = ""
    technologie: str = ""
    cas_utilisation: List[str] = Field(default_factory=list)  # Règle 5
    depend_de: List[str] = Field(default_factory=list)
    source: SourceType = SourceType.HUMAIN


class Attribut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nom: str = ""
    type: str = ""
    obligatoire: bool = True
    donnee_personnelle: bool = False  # Règle 8
    cle: str = ""  # "" | primaire | etrangere
    unique: bool = False
    reference: str = ""  # ENT-xx visée par une clé étrangère
    sur_suppression: str = ""  # cascade | protect | set_null | restrict


class Contrainte(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str = "unique"  # unique | check | index
    champs: List[str] = Field(default_factory=list)
    nom: str = ""
    condition: str = ""


class Relation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    vers: str = ""
    cardinalite: str = ""


class Entite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    table: str = ""  # nom physique ; à défaut, dérivé du nom
    attributs: List[Attribut] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
    contraintes: List[Contrainte] = Field(default_factory=list)
    source: SourceType = SourceType.HUMAIN


class InterfaceExterne(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    systeme: str = ""
    sens: InterfaceDirection = InterfaceDirection.ENTRANT
    protocole: str = ""
    donnees_echangees: str = ""
    proprietaire: str = ""


class Noeud(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    type: str = "conteneur"  # serveur | conteneur | service_gere
    heberge: List[str] = Field(default_factory=list)
    reseau: str = "intranet"  # intranet | dmz | externe


class Deploiement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    environnements: List[str] = Field(default_factory=list)
    noeuds: List[Noeud] = Field(default_factory=list)


class Securite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    authentification: str = ""
    autorisation: str = ""
    chiffrement_transit: str = ""
    chiffrement_repos: str = ""
    journalisation: str = ""


class DiagrammeRef(BaseModel):
    model_config = ConfigDict(extra="ignore")
    fichier: str = ""
    type: str = ""
    cas_utilisation: Optional[str] = None


class Migration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nom: str = ""
    lot: str = ""
    operations: List[str] = Field(default_factory=list)
    reversible: bool = True
    reprise_donnees: str = ""
    statut: str = "prevue"  # prevue | appliquee


class ArchitectureDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document: DocumentHeader
    decisions: List[Decision] = Field(default_factory=list)
    composants: List[Composant] = Field(default_factory=list)
    entites: List[Entite] = Field(default_factory=list)
    interfaces_externes: List[InterfaceExterne] = Field(default_factory=list)
    deploiement: Optional[Deploiement] = None
    securite: Optional[Securite] = None
    diagrammes: List[DiagrammeRef] = Field(default_factory=list)
    migrations: List[Migration] = Field(default_factory=list)
