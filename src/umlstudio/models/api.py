"""Opérations lues dans le contrat d'API (api/openapi.yaml)."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Champ(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nom: str
    type: str = ""
    emplacement: str = "corps"  # corps | chemin | requete | en-tete | cookie
    requis: bool = False


class Reponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str
    description: str = ""


class EffetBdd(BaseModel):
    model_config = ConfigDict(extra="ignore")
    entite: str
    action: str = "ecriture"  # insert | update | delete | lecture | ecriture (non précisé)
    champs: List[str] = Field(default_factory=list)
    detail: str = ""


class Operation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    operation_id: str
    methode: str
    chemin: str
    resume: str = ""
    securite: List[str] = Field(default_factory=list)  # alternatives : une suffit
    champs: List[Champ] = Field(default_factory=list)
    succes: List[Reponse] = Field(default_factory=list)
    erreurs: List[Reponse] = Field(default_factory=list)
    # Extension x-stocke : None = non déclaré, [] = rien n'est stocké, sinon les entités écrites.
    stocke: Optional[List[str]] = None
    # x-stocke détaillé et x-lit : ce que l'appel fait en base, dans l'ordre.
    effets: List[EffetBdd] = Field(default_factory=list)
    transaction: Optional[bool] = None  # x-transaction
