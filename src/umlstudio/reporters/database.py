"""Volet base de données : schéma entité-relation et effets des appels d'API sur les tables."""

import re
import unicodedata
from html import escape
from typing import Dict, List, Optional, Tuple

from ..models.api import Operation
from ..models.architecture import Entite
from ..models.dossier import ConceptionDossier
from .diagrams import ACCENT, BOX_FILL, INK, LINE, MUTED, _svg, _text_block, _text_left, _wrap

SQL_ACTIONS = {
    "insert": "INSERT dans",
    "update": "UPDATE de",
    "delete": "DELETE dans",
    "lecture": "SELECT dans",
    "ecriture": "Écriture (INSERT ou UPDATE non précisé) dans",
}
ON_DELETE = {
    "cascade": "CASCADE : supprime aussi les lignes liées de {table} ({champ})",
    "protect": "Refusé tant que des lignes de {table} y renvoient ({champ})",
    "restrict": "Refusé tant que des lignes de {table} y renvoient ({champ})",
    "set_null": "{table}.{champ} est mis à NULL",
}


def table_name(ent: Entite) -> str:
    """Nom physique de la table : déclaré, sinon dérivé du nom de l'entité (snake_case)."""
    if ent.table.strip():
        return ent.table.strip()
    text = unicodedata.normalize("NFKD", ent.nom)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower() or ent.id.lower().replace("-", "_")


def _entities(dossier: ConceptionDossier) -> Dict[str, Entite]:
    return {e.id: e for e in (dossier.architecture.entites if dossier.architecture else [])}


def _write_checks(ent: Entite, entites: Dict[str, Entite], champs: List[str]) -> List[str]:
    """Contraintes que la base vérifie quand on écrit dans cette table."""
    touched = set(champs)
    checks = []
    not_null = [a.nom for a in ent.attributs if a.obligatoire and a.cle != "primaire" and (not touched or a.nom in touched)]
    if not_null:
        checks.append(f"NOT NULL : {', '.join(not_null)}")
    uniques = [a.nom for a in ent.attributs if a.unique and (not touched or a.nom in touched)]
    uniques += [
        f"{c.nom or '+'.join(c.champs)} ({', '.join(c.champs)})"
        for c in ent.contraintes
        if c.type == "unique" and (not touched or touched & set(c.champs))
    ]
    if uniques:
        checks.append(f"UNIQUE : {', '.join(uniques)} — un doublon fait échouer l'écriture")
    fks = [
        f"{a.nom} → {table_name(entites[a.reference]) if a.reference in entites else a.reference}"
        for a in ent.attributs
        if a.reference and (not touched or a.nom in touched)
    ]
    if fks:
        checks.append(f"Clé étrangère : {', '.join(fks)} doit exister")
    checks += [f"CHECK : {c.condition or c.nom}" for c in ent.contraintes if c.type == "check"]
    return checks


def _delete_effects(ent: Entite, entites: Dict[str, Entite]) -> List[str]:
    """Ce que la suppression d'une ligne déclenche dans les tables qui la référencent."""
    effects = []
    for other in entites.values():
        for attr in other.attributs:
            if attr.reference == ent.id:
                template = ON_DELETE.get(attr.sur_suppression, "Comportement à la suppression non déclaré pour {table}.{champ}")
                effects.append(template.format(table=table_name(other), champ=attr.nom))
    return effects


def operation_db_effects(op: Operation, dossier: ConceptionDossier) -> List[Tuple[str, List[str]]]:
    """Effets d'un appel sur la base : (action sur une table, contraintes et cascades)."""
    entites = _entities(dossier)
    effects: List[Tuple[str, List[str]]] = []
    if op.transaction is True:
        effects.append(("Transaction : tout ou rien, annulée si une étape échoue", []))
    elif op.transaction is False and len([e for e in op.effets if e.action != "lecture"]) > 1:
        effects.append(("Sans transaction : une écriture peut rester si la suivante échoue", []))

    for effet in op.effets:
        ent = entites.get(effet.entite)
        table = table_name(ent) if ent else effet.entite
        title = f"{SQL_ACTIONS.get(effet.action, effet.action)} {table}"
        if effet.champs:
            title += f" ({', '.join(effet.champs)})"
        details = [effet.detail] if effet.detail else []
        if ent and effet.action in ("insert", "update", "ecriture"):
            details += _write_checks(ent, entites, effet.champs if effet.action == "update" else [])
        if ent and effet.action == "delete":
            details += _delete_effects(ent, entites)
        effects.append((title, details))
    return effects


# --- Schéma entité-relation ----------------------------------------------------------------------


def _badges(attr) -> str:
    badges = []
    if attr.cle == "primaire":
        badges.append("PK")
    if attr.cle == "etrangere" or attr.reference:
        badges.append("FK")
    if attr.unique:
        badges.append("UQ")
    if attr.obligatoire and attr.cle != "primaire":
        badges.append("NN")
    return " ".join(badges)


def erd_svg(dossier: ConceptionDossier) -> str:
    """Tables, colonnes et clés ; une flèche par clé étrangère, pointillée pour une relation sans clé déclarée."""
    entites = [e for e in _entities(dossier).values() if e.nom.strip() or e.table.strip()]
    if not entites:
        return ""

    per_row, gap_x, gap_y, head_h, row_h = 3, 90, 50, 46, 22
    # Largeur commune, calée sur le plus long nom de colonne et le plus long type.
    name_w = max([len(a.nom) for e in entites for a in e.attributs] + [8]) * 7.4 + 24
    type_w = max([len(a.type or "-") for e in entites for a in e.attributs] + [6]) * 6.2 + 16
    box_w = max(260, int(name_w + type_w + 56))
    if box_w > 300:  # au-delà, trois boîtes par rangée rendraient le texte illisible une fois la page ajustée
        per_row = 2
    cols = min(per_row, len(entites))
    rows = [entites[i:i + per_row] for i in range(0, len(entites), per_row)]
    heights = [max(head_h + row_h * max(len(e.attributs), 1) + 10 for e in row) for row in rows]
    width = cols * box_w + (cols - 1) * gap_x + 40
    height = sum(heights) + gap_y * (len(rows) - 1) + 40

    pos: Dict[str, Tuple[float, float, float]] = {}
    arc = 36  # place au-dessus de chaque rangée pour les liens qui enjambent une table
    height += arc * len(rows)
    col_of: Dict[str, Tuple[int, int]] = {}
    y = 20.0 + arc
    for r, (row, row_h_total) in enumerate(zip(rows, heights)):
        for i, ent in enumerate(row):
            pos[ent.id] = (20 + i * (box_w + gap_x), y, head_h + row_h * max(len(ent.attributs), 1) + 10)
            col_of[ent.id] = (r, i)
        y += row_h_total + gap_y + arc

    parts: List[str] = []
    by_id = {e.id: e for e in entites}

    def anchor(src: str, src_y: float, dst: str) -> str:
        sx, sy, _ = pos[src]
        dx, dy, _ = pos[dst]
        (sr, sc), (dr, dc) = col_of[src], col_of[dst]
        if sr == dr and abs(sc - dc) > 1:  # même rangée, tables non voisines : arc par-dessus
            x1, x2, top = sx + box_w / 2, dx + box_w / 2, min(sy, dy) - arc + 6
            return f"M{x1:.0f},{sy:.0f} C{x1:.0f},{top:.0f} {x2:.0f},{top:.0f} {x2:.0f},{dy - 2:.0f}"
        y1, y2 = src_y, dy + head_h / 2
        if dx > sx:
            x1, x2 = sx + box_w, dx
        elif dx < sx:
            x1, x2 = sx, dx + box_w
        else:  # même colonne : on contourne par la droite
            x1 = x2 = sx + box_w
            return f"M{x1:.0f},{y1:.0f} C{x1 + 60:.0f},{y1:.0f} {x2 + 60:.0f},{y2:.0f} {x2:.0f},{y2:.0f}"
        bend = (x2 - x1) / 2
        return f"M{x1:.0f},{y1:.0f} C{x1 + bend:.0f},{y1:.0f} {x2 - bend:.0f},{y2:.0f} {x2:.0f},{y2:.0f}"

    linked = {(e.id, a.reference) for e in entites for a in e.attributs if a.reference in by_id}
    # Une couleur par table visée : on suit une flèche jusqu'à sa table même quand elle croise les autres.
    targets = sorted({a.reference for e in entites for a in e.attributs if a.reference in by_id}, key=list(by_id).index)
    color_of = {t: EDGE_COLORS[i % len(EDGE_COLORS)] for i, t in enumerate(targets)}
    parts.append("<defs>" + "".join(
        f'<marker id="fleche-{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for i, c in enumerate(EDGE_COLORS)) + "</defs>")
    for ent in entites:
        x, top, _ = pos[ent.id]
        for j, attr in enumerate(ent.attributs):
            if attr.reference in by_id and attr.reference != ent.id:
                d = anchor(ent.id, top + head_h + row_h * j + row_h / 2, attr.reference)
                color = color_of[attr.reference]
                parts.append(f'<path data-lien="{escape(ent.id)}&gt;{escape(attr.reference)}" d="{d}" fill="none" '
                             f'stroke="{color}" stroke-width="1.6" opacity="0.85" '
                             f'marker-end="url(#fleche-{EDGE_COLORS.index(color)})"/>')
        for rel in ent.relations:
            if rel.vers in by_id and (rel.vers, ent.id) not in linked and (ent.id, rel.vers) not in linked:
                d = anchor(ent.id, top + head_h / 2, rel.vers)
                parts.append(f'<path data-relation="{escape(ent.id)}&gt;{escape(rel.vers)}" d="{d}" fill="none" stroke="{LINE}" '
                             f'stroke-width="1.2" stroke-dasharray="5 4" marker-end="url(#fleche)"/>')

    for ent in entites:
        x, top, h = pos[ent.id]
        parts.append(f'<rect x="{x}" y="{top:.0f}" width="{box_w}" height="{h:.0f}" rx="8" fill="{BOX_FILL}" stroke="{ACCENT}" stroke-width="1.3"/>')
        parts.append(f'<path d="M{x},{top + head_h:.0f} V{top + 8:.0f} a8,8 0 0 1 8,-8 H{x + box_w - 8} a8,8 0 0 1 8,8 '
                     f'V{top + head_h:.0f} z" fill="{ACCENT}"/>')
        parts.append(_text_block(x + box_w / 2, top + 20, [table_name(ent)], size=13, weight="700", fill="#ffffff"))
        parts.append(_text_block(x + box_w / 2, top + 37, [f"{ent.nom} · {ent.id}"], size=10, fill="#e0e7ff"))
        for j, attr in enumerate(ent.attributs):
            ry = top + head_h + row_h * j
            if j % 2:
                parts.append(f'<rect x="{x + 1}" y="{ry:.0f}" width="{box_w - 2}" height="{row_h}" fill="#f8fafc"/>')
            weight = "700" if attr.cle == "primaire" else "400"
            parts.append(_text_left(x + 10, ry + 15, [attr.nom], size=12, weight=weight, fill=INK, mono=True))
            parts.append(_text_left(x + name_w, ry + 15, [attr.type or "-"], size=11, fill=MUTED))
            badges = _badges(attr)
            if badges:
                parts.append(f'<text x="{x + box_w - 10}" y="{ry + 15:.0f}" text-anchor="end" font-size="10" '
                             f'font-weight="700" fill="{ACCENT}">{escape(badges)}</text>')

    return _svg(width, height, "".join(parts), "diagramme-bdd", "Schéma de la base de données")


def _mermaid_token(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_") or "x"


EDGE_COLORS = ("#4f46e5", "#0891b2", "#c2410c", "#15803d", "#be185d", "#7c3aed")

CARDINALITES = {"1..*": "||--|{", "0..*": "||--o{", "*": "||--o{", "1": "||--||", "1..1": "||--||", "0..1": "||--o|"}


def erd_mermaid(dossier: ConceptionDossier) -> str:
    entites = [e for e in _entities(dossier).values() if e.nom.strip() or e.table.strip()]
    if not entites:
        return ""
    by_id = {e.id: e for e in entites}
    lines = ["erDiagram"]
    for ent in entites:
        lines.append(f"    {_mermaid_token(table_name(ent))} {{")
        for attr in ent.attributs:
            keys = ", ".join(k for k in ("PK" if attr.cle == "primaire" else "",
                                         "FK" if attr.reference else "",
                                         "UK" if attr.unique else "") if k)
            comment = ' "NN"' if attr.obligatoire and attr.cle != "primaire" else ""
            lines.append(f"        {_mermaid_token(attr.type or 'texte')} {_mermaid_token(attr.nom)}{' ' + keys if keys else ''}{comment}")
        lines.append("    }")
    linked = {(e.id, a.reference) for e in entites for a in e.attributs if a.reference in by_id}
    for ent in entites:
        for attr in ent.attributs:
            if attr.reference in by_id:
                lines.append(f'    {_mermaid_token(table_name(by_id[attr.reference]))} ||--o{{ '
                             f'{_mermaid_token(table_name(ent))} : "{_mermaid_token(attr.nom)}"')
    for ent in entites:
        for rel in ent.relations:
            if rel.vers in by_id and (rel.vers, ent.id) not in linked and (ent.id, rel.vers) not in linked:
                lines.append(f'    {_mermaid_token(table_name(ent))} {CARDINALITES.get(rel.cardinalite, "||--o{")} '
                             f'{_mermaid_token(table_name(by_id[rel.vers]))} : "{_mermaid_token(rel.cardinalite or "relation")}"')
    return "\n".join(lines)
