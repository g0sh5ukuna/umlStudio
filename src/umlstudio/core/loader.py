"""Chargeur et analyseur des fichiers du dossier de conception."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from ..models.dossier import ConceptionDossier
from ..models.cadrage import CadrageDocument
from ..models.exigences import ExigencesDocument
from ..models.glossaire import GlossaireDocument
from ..models.architecture import ArchitectureDocument
from ..models.plan import PlanDocument
from ..models.risques import RisquesDocument
from ..models.tests import TestsDocument
from ..models.validations import ValidationsDocument


class LoadError:
    def __init__(self, file_name: str, message: str, is_fatal: bool = False):
        self.file_name = file_name
        self.message = message
        self.is_fatal = is_fatal

    def __repr__(self) -> str:
        return f"LoadError({self.file_name}: {self.message})"


def find_conception_root(target_path: Optional[Path] = None) -> Path:
    """Trouve la racine du dossier de conception selon les conventions du projet."""
    start = target_path or Path.cwd()

    # Si le chemin cible contient directement 00-cadrage.yaml
    if (start / "00-cadrage.yaml").exists():
        return start

    # Si sous-dossier modeles/conception
    if (start / "modeles" / "conception" / "00-cadrage.yaml").exists():
        return start / "modeles" / "conception"

    # Si sous-dossier conception
    if (start / "conception" / "00-cadrage.yaml").exists():
        return start / "conception"

    return start


def safe_load_yaml(file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """Lit et parse un fichier YAML. Retourne (dict_parsed, raw_text, error_message)."""
    if not file_path.is_file():
        return None, None, f"Fichier absent: {file_path.name}"
    try:
        raw_text = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text)
        if not isinstance(data, dict):
            return {}, raw_text, None
        return data, raw_text, None
    except Exception as e:
        return None, None, f"Erreur de syntaxe YAML dans {file_path.name}: {e}"


def extract_openapi_endpoints(api_path: Path) -> List[str]:
    """Extrait la liste des operationIds d'un fichier OpenAPI s'il existe."""
    endpoints: List[str] = []
    openapi_files = [
        api_path / "openapi.yaml",
        api_path / "openapi.yml",
        api_path / "openapi.json",
    ]
    target = next((f for f in openapi_files if f.is_file()), None)
    if not target:
        return endpoints

    try:
        raw = target.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if isinstance(data, dict) and "paths" in data and isinstance(data["paths"], dict):
            for path, path_item in data["paths"].items():
                if isinstance(path_item, dict):
                    for method, op in path_item.items():
                        if isinstance(op, dict):
                            op_id = op.get("operationId")
                            if op_id:
                                endpoints.append(str(op_id))
                            else:
                                endpoints.append(f"{method.upper()} {path}")
    except Exception:
        pass
    return endpoints


def load_dossier(folder_path: Optional[Path] = None) -> Tuple[ConceptionDossier, List[LoadError]]:
    """Charge l'ensemble du dossier de conception et renvoie l'agrégat ainsi que les éventuelles erreurs."""
    root = find_conception_root(folder_path)
    errors: List[LoadError] = []
    raw_files: Dict[str, str] = {}

    dossier = ConceptionDossier(root_path=root)

    # 1. Cadrage
    cadrage_file = root / "00-cadrage.yaml"
    data, raw, err = safe_load_yaml(cadrage_file)
    if err:
        errors.append(LoadError("00-cadrage.yaml", err))
    elif data:
        raw_files["00-cadrage.yaml"] = raw or ""
        try:
            dossier.cadrage = CadrageDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("00-cadrage.yaml", f"Erreur de schéma Pydantic: {e}"))

    # 2. Exigences
    exigences_file = root / "01-exigences.yaml"
    data, raw, err = safe_load_yaml(exigences_file)
    if err:
        errors.append(LoadError("01-exigences.yaml", err))
    elif data:
        raw_files["01-exigences.yaml"] = raw or ""
        try:
            dossier.exigences = ExigencesDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("01-exigences.yaml", f"Erreur de schéma Pydantic: {e}"))

    # 3. Glossaire
    glossaire_file = root / "02-glossaire.yaml"
    data, raw, err = safe_load_yaml(glossaire_file)
    if err:
        errors.append(LoadError("02-glossaire.yaml", err))
    elif data:
        raw_files["02-glossaire.yaml"] = raw or ""
        try:
            dossier.glossaire = GlossaireDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("02-glossaire.yaml", f"Erreur de schéma Pydantic: {e}"))

    # 4. Architecture
    archi_file = root / "03-architecture.yaml"
    data, raw, err = safe_load_yaml(archi_file)
    if err:
        errors.append(LoadError("03-architecture.yaml", err))
    elif data:
        raw_files["03-architecture.yaml"] = raw or ""
        try:
            dossier.architecture = ArchitectureDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("03-architecture.yaml", f"Erreur de schéma Pydantic: {e}"))

    # 5. Plan
    plan_file = root / "04-plan.yaml"
    data, raw, err = safe_load_yaml(plan_file)
    if err:
        errors.append(LoadError("04-plan.yaml", err))
    elif data:
        raw_files["04-plan.yaml"] = raw or ""
        try:
            dossier.plan = PlanDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("04-plan.yaml", f"Erreur de schéma Pydantic: {e}"))

    # 6. Risques
    risques_file = root / "05-risques.yaml"
    data, raw, err = safe_load_yaml(risques_file)
    if err:
        errors.append(LoadError("05-risques.yaml", err))
    elif data:
        raw_files["05-risques.yaml"] = raw or ""
        try:
            dossier.risques = RisquesDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("05-risques.yaml", f"Erreur de schéma Pydantic: {e}"))

    # 7. Tests
    tests_file = root / "06-tests.yaml"
    data, raw, err = safe_load_yaml(tests_file)
    if err:
        errors.append(LoadError("06-tests.yaml", err))
    elif data:
        raw_files["06-tests.yaml"] = raw or ""
        try:
            dossier.tests = TestsDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("06-tests.yaml", f"Erreur de schéma Pydantic: {e}"))

    # 8. Validations
    validations_file = root / "validations.yaml"
    data, raw, err = safe_load_yaml(validations_file)
    if err:
        errors.append(LoadError("validations.yaml", err))
    elif data:
        raw_files["validations.yaml"] = raw or ""
        try:
            dossier.validations = ValidationsDocument.model_validate(data)
        except Exception as e:
            errors.append(LoadError("validations.yaml", f"Erreur de schéma Pydantic: {e}"))

    # OpenAPI endpoints
    api_dir = root / "api"
    if api_dir.is_dir():
        dossier.openapi_endpoints = extract_openapi_endpoints(api_dir)

    dossier.raw_files = raw_files
    return dossier, errors
