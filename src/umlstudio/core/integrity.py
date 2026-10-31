"""Calcul d'intégrité SHA-256 et gestion du registre validations.yaml."""

import hashlib
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

from ..models.validations import ValidationEntry, ValidationsDocument, Validateur


def compute_sha256(file_path: Path) -> str:
    """Calcule l'empreinte SHA-256 d'un fichier."""
    if not file_path.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_current_git_commit(cwd: Path) -> str:
    """Récupère le hash du commit git courant s'il existe."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return ""


def audit_validations(dossier_path: Path, validations_doc: Optional[ValidationsDocument]) -> List[Dict[str, str]]:
    """Vérifie l'intégrité de chaque entrée de validation par rapport aux fichiers réels."""
    anomalies: List[Dict[str, str]] = []
    if not validations_doc:
        return anomalies

    for val in validations_doc.validations:
        if not val.document:
            continue
        target_path = dossier_path / val.document
        if not target_path.exists():
            anomalies.append({
                "document": val.document,
                "type": "FICHIER_INTROUVABLE",
                "message": f"Le document validé '{val.document}' n'existe pas sur le disque.",
            })
            continue

        current_hash = compute_sha256(target_path)
        if val.sha256 and current_hash != val.sha256:
            anomalies.append({
                "document": val.document,
                "type": "HASH_MISMATCH",
                "message": (
                    f"Le fichier '{val.document}' a été modifié depuis sa validation ! "
                    f"SHA-256 validé: {val.sha256[:10]}... != actuel: {current_hash[:10]}..."
                ),
            })
        elif not val.sha256:
            anomalies.append({
                "document": val.document,
                "type": "HASH_MANQUANT",
                "message": f"Le document '{val.document}' a une entrée dans validations.yaml mais pas de hash sha256.",
            })

    return anomalies


def sign_document(
    dossier_path: Path,
    document_rel_name: str,
    author_name: str = "",
    author_role: str = "",
    evidence_url: str = "",
    version: str = "0.1.0",
    reserves: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """Calcule le SHA-256 du document et met à jour validations.yaml."""
    target_file = dossier_path / document_rel_name
    if not target_file.resolve().is_relative_to(dossier_path.resolve()):
        return False, f"Refusé : '{document_rel_name}' est hors du dossier de conception."
    if not author_name.strip():
        return False, "Refusé : l'auteur de la validation est obligatoire (--author)."
    if not evidence_url.strip():
        return False, "Refusé : la preuve d'approbation est obligatoire (--evidence, ex : lien de la PR)."
    if not target_file.is_file():
        return False, f"Fichier introuvable : {target_file}"

    file_hash = compute_sha256(target_file)
    commit_sha = get_current_git_commit(dossier_path)
    today_str = date.today().isoformat()

    validations_file = dossier_path / "validations.yaml"
    existing_data: Dict = {}
    if validations_file.is_file():
        with open(validations_file, "r", encoding="utf-8") as f:
            try:
                existing_data = yaml.safe_load(f) or {}
            except Exception as e:
                return False, f"Erreur lors de la lecture de {validations_file}: {e}"

    entries = existing_data.get("validations", [])
    if not isinstance(entries, list):
        entries = []

    # Chercher si une entrée existe déjà pour ce document
    updated = False
    new_entry = {
        "document": document_rel_name,
        "version": version,
        "sha256": file_hash,
        "commit": commit_sha,
        "validateur": {
            "nom": author_name,
            "role": author_role,
        },
        "date": today_str,
        "preuve": evidence_url,
        "reserves": reserves or [],
    }

    for i, entry in enumerate(entries):
        if entry.get("document") == document_rel_name:
            entries[i] = new_entry
            updated = True
            break

    if not updated:
        entries.append(new_entry)

    existing_data["validations"] = entries

    with open(validations_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(existing_data, f, allow_unicode=True, sort_keys=False)

    action = "mise à jour" if updated else "enregistrée"
    return True, f"Validation {action} pour '{document_rel_name}' (SHA-256: {file_hash[:12]}...)"
