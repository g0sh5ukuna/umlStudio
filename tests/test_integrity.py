"""Tests unitaires pour l'intégrité SHA-256 et la validation (Règle 11)."""

from pathlib import Path
from umlstudio.core.integrity import compute_sha256, audit_validations, sign_document
from umlstudio.models.validations import ValidationsDocument, ValidationEntry


def test_compute_sha256(tmp_path: Path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello umlStudio", encoding="utf-8")
    hash1 = compute_sha256(f)
    assert len(hash1) == 64

    # Modification du fichier -> hash différent
    f.write_text("Hello umlStudio modified", encoding="utf-8")
    hash2 = compute_sha256(f)
    assert hash1 != hash2


def test_audit_validations_hash_mismatch(tmp_path: Path):
    doc_file = tmp_path / "00-cadrage.yaml"
    doc_file.write_text("version: 1", encoding="utf-8")
    actual_hash = compute_sha256(doc_file)

    val_doc = ValidationsDocument(
        validations=[
            ValidationEntry(
                document="00-cadrage.yaml",
                sha256="wrong_hash_00000000000000000000000000000000000000000000000000000000",
            )
        ]
    )

    anomalies = audit_validations(tmp_path, val_doc)
    assert len(anomalies) == 1
    assert anomalies[0]["type"] == "HASH_MISMATCH"


def test_sign_and_audit_success(tmp_path: Path):
    doc_file = tmp_path / "00-cadrage.yaml"
    doc_file.write_text("statut: valide\ncontexte: OK", encoding="utf-8")

    success, msg = sign_document(
        dossier_path=tmp_path,
        document_rel_name="00-cadrage.yaml",
        author_name="Alice",
        author_role="Lead Tech",
        evidence_url="PR #1",
    )
    assert success
    assert "00-cadrage.yaml" in msg

    # Recharger et auditer
    val_file = tmp_path / "validations.yaml"
    assert val_file.is_file()

    import yaml
    with open(val_file, "r") as f:
        data = yaml.safe_load(f)

    val_doc = ValidationsDocument.model_validate(data)
    anomalies = audit_validations(tmp_path, val_doc)
    assert len(anomalies) == 0


def test_sign_refuse_un_chemin_hors_du_dossier(tmp_path: Path):
    dossier = tmp_path / "conception"
    dossier.mkdir()
    (tmp_path / "secret.txt").write_text("hors dossier", encoding="utf-8")

    success, msg = sign_document(
        dossier_path=dossier,
        document_rel_name="../secret.txt",
        author_name="Alice",
        evidence_url="PR #1",
    )
    assert not success
    assert "hors du dossier" in msg
    assert not (dossier / "validations.yaml").exists()


def test_sign_exige_un_auteur_et_une_preuve(tmp_path: Path):
    (tmp_path / "00-cadrage.yaml").write_text("contexte: OK", encoding="utf-8")

    success, msg = sign_document(tmp_path, "00-cadrage.yaml", author_name="", evidence_url="PR #1")
    assert not success
    assert "auteur" in msg

    success, msg = sign_document(tmp_path, "00-cadrage.yaml", author_name="Alice", evidence_url="  ")
    assert not success
    assert "preuve" in msg
    assert not (tmp_path / "validations.yaml").exists()
