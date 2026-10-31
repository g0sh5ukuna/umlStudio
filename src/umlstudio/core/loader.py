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
from ..models.api import Champ, EffetBdd, Operation, Reponse


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


HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")
EMPLACEMENTS = {"path": "chemin", "query": "requete", "header": "en-tete", "cookie": "cookie"}
CONTENT_TYPES = ("application/json", "multipart/form-data", "application/x-www-form-urlencoded")


def _resolve(spec: Dict[str, Any], node: Any) -> Any:
    """Suit les références locales ($ref: "#/components/...")."""
    seen = 0
    while isinstance(node, dict) and isinstance(node.get("$ref"), str) and node["$ref"].startswith("#/") and seen < 20:
        target: Any = spec
        for part in node["$ref"][2:].split("/"):
            target = target.get(part, {}) if isinstance(target, dict) else {}
        node, seen = target, seen + 1
    return node if isinstance(node, dict) else {}


def _schema_type(spec: Dict[str, Any], schema: Any) -> str:
    schema = _resolve(spec, schema)
    if schema.get("format") == "binary":
        return "fichier"
    kind = schema.get("type", "")
    if isinstance(kind, list):  # OpenAPI 3.1 : ["string", "null"]
        kind = next((k for k in kind if k != "null"), "")
    if kind == "array":
        return f"liste de {_schema_type(spec, schema.get('items', {})) or 'valeurs'}"
    if schema.get("format") and kind == "string":
        return f"string ({schema['format']})"
    return kind or ("objet" if "properties" in schema else "")


def _body_fields(spec: Dict[str, Any], schema: Any) -> List[Champ]:
    schema = _resolve(spec, schema)
    properties: Dict[str, Any] = dict(schema.get("properties", {}) or {})
    required = set(schema.get("required", []) or [])
    for part in schema.get("allOf", []) or []:
        part = _resolve(spec, part)
        properties.update(part.get("properties", {}) or {})
        required |= set(part.get("required", []) or [])
    return [
        Champ(nom=name, type=_schema_type(spec, prop), emplacement="corps", requis=name in required)
        for name, prop in properties.items()
    ]


def _security_labels(spec: Dict[str, Any], requirements: Any) -> List[str]:
    """Traduit les exigences de sécurité OpenAPI ; chaque élément de la liste est une alternative."""
    if requirements is None:
        return []
    if requirements == [] or requirements == [{}]:
        return ["Public"]
    schemes = (spec.get("components", {}) or {}).get("securitySchemes", {}) or {}
    labels = []
    for requirement in requirements:
        parts = []
        for name, scopes in (requirement or {}).items():
            scheme = _resolve(spec, schemes.get(name, {}))
            kind = scheme.get("type")
            if kind == "http" and str(scheme.get("scheme", "")).lower() == "bearer":
                label = "JWT (Bearer)" if str(scheme.get("bearerFormat", "")).upper() == "JWT" else "Jeton Bearer"
            elif kind == "http":
                label = f"HTTP {str(scheme.get('scheme', '')).capitalize()}"
            elif kind == "apiKey" and scheme.get("in") == "cookie":
                label = f"Cookie {scheme.get('name', name)}"
            elif kind == "apiKey":
                where = {"header": "en-tête", "query": "paramètre"}.get(scheme.get("in", ""), scheme.get("in", ""))
                label = f"Clé API ({where} {scheme.get('name', name)})"
            elif kind == "oauth2":
                label = f"OAuth2 ({', '.join(scopes)})" if scopes else "OAuth2"
            elif kind == "openIdConnect":
                label = "OpenID Connect"
            else:
                label = name
            parts.append(label)
        labels.append(" + ".join(parts) or "Public")
    return labels


def extract_openapi_operations(api_path: Path) -> List[Operation]:
    """Lit les opérations du contrat OpenAPI : méthode, sécurité, champs, réponses et stockage (x-stocke)."""
    target = next((api_path / f for f in ("openapi.yaml", "openapi.yml", "openapi.json") if (api_path / f).is_file()), None)
    if not target:
        return []
    try:
        spec = yaml.safe_load(target.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(spec, dict) or not isinstance(spec.get("paths"), dict):
        return []

    operations: List[Operation] = []
    for path, path_item in spec["paths"].items():
        path_item = _resolve(spec, path_item)
        shared_params = path_item.get("parameters", []) or []
        for method in HTTP_METHODS:
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue

            params: Dict[Tuple[str, str], Champ] = {}
            for raw in [*shared_params, *(op.get("parameters", []) or [])]:
                param = _resolve(spec, raw)
                if param.get("name"):
                    params[(param["name"], param.get("in", ""))] = Champ(
                        nom=param["name"],
                        type=_schema_type(spec, param.get("schema", {})),
                        emplacement=EMPLACEMENTS.get(param.get("in", ""), param.get("in", "")),
                        requis=bool(param.get("required")) or param.get("in") == "path",
                    )
            champs = list(params.values())
            content = _resolve(spec, op.get("requestBody", {})).get("content", {}) or {}
            media = next((content[c] for c in CONTENT_TYPES if c in content), next(iter(content.values()), None))
            if isinstance(media, dict):
                champs += _body_fields(spec, media.get("schema", {}))

            succes, erreurs = [], []
            for code, response in (op.get("responses", {}) or {}).items():
                reponse = Reponse(code=str(code), description=_resolve(spec, response).get("description", ""))
                (succes if str(code)[:1] in "123" else erreurs).append(reponse)

            effets: List[EffetBdd] = []
            stocke_brut = op.get("x-stocke")
            for item in stocke_brut if isinstance(stocke_brut, list) else []:
                if isinstance(item, dict) and item.get("entite"):
                    effets.append(EffetBdd.model_validate({**item, "entite": str(item["entite"])}))
                elif isinstance(item, (str, int)):
                    effets.append(EffetBdd(entite=str(item)))
            # Les lectures précèdent les écritures : on lit avant de décider quoi écrire.
            lectures = op.get("x-lit")
            effets = [EffetBdd(entite=str(e), action="lecture") for e in (lectures if isinstance(lectures, list) else [])] + effets
            stocke = [e.entite for e in effets if e.action != "lecture"] if isinstance(stocke_brut, list) else None
            transaction = op.get("x-transaction")
            operations.append(
                Operation(
                    operation_id=str(op.get("operationId") or f"{method.upper()} {path}"),
                    methode=method.upper(),
                    chemin=path,
                    resume=op.get("summary", "") or "",
                    securite=_security_labels(spec, op["security"] if "security" in op else spec.get("security")),
                    champs=champs,
                    succes=succes,
                    erreurs=erreurs,
                    stocke=stocke,
                    effets=effets,
                    transaction=transaction if isinstance(transaction, bool) else None,
                )
            )
    return operations


def extract_openapi_endpoints(api_path: Path) -> List[str]:
    """Extrait la liste des operationIds d'un fichier OpenAPI s'il existe."""
    return [op.operation_id for op in extract_openapi_operations(api_path)]


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
        dossier.operations = extract_openapi_operations(api_dir)
        dossier.openapi_endpoints = [op.operation_id for op in dossier.operations]

    dossier.raw_files = raw_files
    return dossier, errors
