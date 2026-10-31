"""Diagrammes générés depuis le dossier : couloirs par cas d'utilisation et vue de bout en bout.

Le HTML reçoit du SVG en ligne (aucune bibliothèque, lisible hors connexion et à l'impression),
le Markdown reçoit du Mermaid (rendu nativement par GitHub et GitLab).
"""

import re
import unicodedata
from html import escape
from typing import Dict, List, Optional, Sequence, Tuple

from ..models.api import Champ, Operation
from ..models.architecture import Composant
from ..models.dossier import ConceptionDossier
from ..models.exigences import Acteur, CasUtilisation

SYSTEME = "Système"

# Palette commune aux deux diagrammes.
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#94a3b8"
ACCENT = "#4f46e5"
LANE_FILLS = ("#f8fafc", "#eef2ff")
BOX_FILL = "#ffffff"


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def _step_text(step: str) -> str:
    """Retire la numérotation ("1. ") d'une étape."""
    return re.sub(r"^\s*\d+[.)]?\s*", "", step or "").strip()


def _wrap(text: str, width: int) -> List[str]:
    lines: List[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _text_block(x: float, y: float, lines: Sequence[str], size: int = 12, weight: str = "400", fill: str = INK) -> str:
    tspans = "".join(
        f'<tspan x="{x:.0f}" dy="{0 if i == 0 else size + 4}">{escape(line)}</tspan>' for i, line in enumerate(lines)
    )
    return f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" font-size="{size}" font-weight="{weight}" fill="{fill}">{tspans}</text>'


def _svg(width: float, height: float, body: str, css_class: str, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="{css_class}" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="100%" style="max-width:{width:.0f}px;height:auto" role="img" aria-label="{escape(title)}" '
        f'font-family="system-ui, sans-serif">'
        f"<title>{escape(title)}</title>"
        f'<defs><marker id="fleche" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker></defs>'
        f"{body}</svg>"
    )


# --- Couloirs (lignes d'eau) d'un cas d'utilisation ---------------------------------------------


def assign_lanes(steps: Sequence[str], acteurs: Sequence[Acteur], default: str) -> List[str]:
    """Attribue chaque étape au couloir de son sujet.

    Le sujet est l'acteur (ou « le système ») cité le plus tôt dans l'étape.
    Une étape sans sujet reconnu (« Il valide ») reste dans le couloir de l'étape précédente.
    """
    candidates = [(a.nom, re.compile(rf"\b{re.escape(_norm(a.nom))}\b")) for a in acteurs if a.nom.strip()]
    candidates.append((SYSTEME, re.compile(r"\bsysteme\b")))

    lanes: List[str] = []
    previous = default
    for step in steps:
        text = _norm(_step_text(step))
        hits = [(m.start(), name) for name, pattern in candidates if (m := pattern.search(text))]
        previous = min(hits)[1] if hits else previous
        lanes.append(previous)
    return lanes


def _swimlane_model(uc: CasUtilisation, acteurs: Dict[str, Acteur]) -> Optional[Tuple[List[str], List[str], List[str]]]:
    steps = [_step_text(s) for s in uc.scenario_nominal if _step_text(s)]
    if not steps:
        return None

    declared = [acteurs[i].nom for i in [uc.acteur_principal, *uc.acteurs_secondaires] if i in acteurs and acteurs[i].nom]
    default = declared[0] if declared else SYSTEME
    step_lanes = assign_lanes(steps, list(acteurs.values()), default)

    # Couloirs : acteurs déclarés, puis acteurs cités, puis le système s'il agit.
    lanes = list(dict.fromkeys(declared))
    lanes += [lane for lane in dict.fromkeys(step_lanes) if lane not in lanes and lane != SYSTEME]
    if SYSTEME in step_lanes:
        lanes.append(SYSTEME)
    return lanes, steps, step_lanes


def swimlane_svg(uc: CasUtilisation, acteurs: Dict[str, Acteur]) -> str:
    """Diagramme en couloirs du scénario nominal : une colonne par acteur, lecture de haut en bas."""
    model = _swimlane_model(uc, acteurs)
    if not model:
        return ""
    lanes, steps, step_lanes = model

    lane_w, header_h, box_w, gap, pad_top = 200, 40, 168, 30, 26
    col = {lane: i for i, lane in enumerate(lanes)}
    width = lane_w * len(lanes)

    boxes = []
    y = header_h + pad_top
    for i, (text, lane) in enumerate(zip(steps, step_lanes)):
        lines = _wrap(text, 24)
        h = 20 + 16 * len(lines)
        boxes.append((col[lane] * lane_w + lane_w / 2, y, h, lines, i + 1))
        y += h + gap
    height = y + 10

    parts = []
    for i, lane in enumerate(lanes):
        x = i * lane_w
        parts.append(f'<rect x="{x}" y="0" width="{lane_w}" height="{height:.0f}" fill="{LANE_FILLS[i % 2]}"/>')
        parts.append(f'<rect x="{x}" y="0" width="{lane_w}" height="{header_h}" fill="{ACCENT}" opacity="{0.92 if i % 2 else 1}"/>')
        parts.append(_text_block(x + lane_w / 2, 25, _wrap(lane, 22)[:1], size=13, weight="700", fill="#ffffff"))
        if i:
            parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height:.0f}" stroke="{LINE}" stroke-dasharray="4 4"/>')

    for (cx, top, h, _, _), (nx, ntop, _, _, _) in zip(boxes, boxes[1:]):
        bottom, mid = top + h, top + h + gap / 2
        if cx == nx:
            d = f"M{cx:.0f},{bottom:.0f} L{nx:.0f},{ntop - 2:.0f}"
        else:
            d = f"M{cx:.0f},{bottom:.0f} L{cx:.0f},{mid:.0f} L{nx:.0f},{mid:.0f} L{nx:.0f},{ntop - 2:.0f}"
        parts.append(f'<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#fleche)"/>')

    for cx, top, h, lines, n in boxes:
        parts.append(
            f'<rect x="{cx - box_w / 2:.0f}" y="{top:.0f}" width="{box_w}" height="{h}" rx="8" '
            f'fill="{BOX_FILL}" stroke="{ACCENT}" stroke-width="1.2"/>'
        )
        parts.append(f'<circle cx="{cx - box_w / 2:.0f}" cy="{top:.0f}" r="10" fill="{ACCENT}"/>')
        parts.append(_text_block(cx - box_w / 2, top + 4, [str(n)], size=11, weight="700", fill="#ffffff"))
        parts.append(_text_block(cx, top + 22, lines))

    return _svg(width, height, "".join(parts), "diagramme-couloirs", f"{uc.id} — {uc.nom}")


def _mermaid_label(text: str) -> str:
    return re.sub(r"[;#\n\r]", ",", text).replace('"', "'").strip()


def swimlane_mermaid(uc: CasUtilisation, acteurs: Dict[str, Acteur]) -> str:
    """Même scénario en diagramme de séquence Mermaid : chaque passage de couloir est une flèche."""
    model = _swimlane_model(uc, acteurs)
    if not model:
        return ""
    lanes, steps, step_lanes = model
    alias = {lane: f"L{i}" for i, lane in enumerate(lanes)}

    lines = ["sequenceDiagram"]
    lines += [f"    participant {alias[lane]} as {_mermaid_label(lane)}" for lane in lanes]
    previous = step_lanes[0]
    for n, (text, lane) in enumerate(zip(steps, step_lanes), start=1):
        label = _mermaid_label(f"{n}. {text}")
        if n == 1:
            lines.append(f"    Note over {alias[lane]}: {label}")
        else:
            lines.append(f"    {alias[previous]}->>{alias[lane]}: {label}")
        previous = lane
    return "\n".join(lines)


# --- Vue de bout en bout -------------------------------------------------------------------------

COLUMNS = (
    ("acteurs", "Acteurs"),
    ("presentation", "Présentation"),
    ("application", "Application"),
    ("donnees", "Données & infrastructure"),
    ("externes", "Systèmes externes"),
)


def _architecture_model(dossier: ConceptionDossier) -> Optional[Tuple[Dict[str, List[Tuple[str, str]]], List[Tuple[str, str]]]]:
    if not dossier.architecture or not dossier.architecture.composants:
        return None

    composants = [c for c in dossier.architecture.composants if c.nom.strip()]
    if not composants:
        return None
    acteurs =[a for a in (dossier.exigences.acteurs if dossier.exigences else []) if a.nom.strip()]
    ucs = dossier.exigences.cas_utilisation if dossier.exigences else []

    columns: Dict[str, List[Tuple[str, str]]] = {key: [] for key, _ in COLUMNS}
    for a in acteurs:
        columns["externes" if a.type == "systeme" else "acteurs"].append((a.id, a.nom))
    for c in composants:
        key = "donnees" if c.couche in ("donnees", "infrastructure") else c.couche
        columns.setdefault(key, []).append((c.id, c.nom))

    def covering(uc_ids: set, couches: Tuple[str, ...]) -> List[Composant]:
        return [c for c in composants if c.couche in couches and uc_ids & set(c.cas_utilisation)]

    edges: List[Tuple[str, str]] = []
    for a in acteurs:
        uc_ids = {u.id for u in ucs if a.id == u.acteur_principal or a.id in u.acteurs_secondaires}
        # Un humain entre par la présentation ; un système externe parle à l'application.
        preferred = ("application",) if a.type == "systeme" else ("presentation",)
        targets = covering(uc_ids, preferred) or covering(uc_ids, ("presentation", "application"))
        edges += [(a.id, c.id) for c in targets]
    known = {c.id for c in composants}
    for c in composants:
        edges += [(c.id, dep) for dep in c.depend_de if dep in known]
    return columns, list(dict.fromkeys(edges))


def architecture_svg(dossier: ConceptionDossier) -> str:
    """Acteurs, composants par couche et systèmes externes, reliés par les cas d'utilisation et les dépendances."""
    model = _architecture_model(dossier)
    if not model:
        return ""
    columns, edges = model

    col_w, gap, box_h, box_gap, header_h = 180, 70, 60, 18, 44
    visible = [(key, title) for key, title in COLUMNS if columns.get(key)]
    pos: Dict[str, Tuple[float, float, int]] = {}
    parts: List[str] = []
    tallest = max(len(columns[key]) for key, _ in visible)
    height = header_h + tallest * (box_h + box_gap) + 20
    width = len(visible) * col_w + (len(visible) - 1) * gap

    for i, (key, title) in enumerate(visible):
        x = i * (col_w + gap)
        parts.append(f'<rect x="{x}" y="0" width="{col_w}" height="{height}" rx="10" fill="{LANE_FILLS[i % 2]}"/>')
        parts.append(_text_block(x + col_w / 2, 26, [title], size=13, weight="700", fill=ACCENT))
        for j, (item_id, _) in enumerate(columns[key]):
            pos[item_id] = (x, header_h + j * (box_h + box_gap), i)

    for src, dst in edges:
        sx, sy, si = pos[src]
        dx, dy, di = pos[dst]
        y1, y2 = sy + box_h / 2, dy + box_h / 2
        if di > si:
            x1, x2 = sx + col_w, dx
        elif di < si:
            x1, x2 = sx, dx + col_w
        else:  # même colonne : une boucle par la droite
            x1 = x2 = sx + col_w
        bend = max(abs(x2 - x1) / 2, 40) * (1 if x2 >= x1 or di == si else -1)
        d = f"M{x1:.0f},{y1:.0f} C{x1 + bend:.0f},{y1:.0f} {x2 - bend if di != si else x2 + bend:.0f},{y2:.0f} {x2:.0f},{y2:.0f}"
        # Un lien qui saute une colonne passe derrière ses boîtes : pointillé et plus clair pour ne pas le confondre.
        style = ' stroke-dasharray="5 4" opacity="0.45"' if abs(di - si) > 1 else ' opacity="0.8"'
        parts.append(
            f'<path data-lien="{escape(src)}&gt;{escape(dst)}" d="{d}" fill="none" stroke="{MUTED}" '
            f'stroke-width="1.3"{style} marker-end="url(#fleche)"/>'
        )

    for key, _ in visible:
        for item_id, name in columns[key]:
            x, y, _ = pos[item_id]
            parts.append(
                f'<rect x="{x + 8}" y="{y}" width="{col_w - 16}" height="{box_h}" rx="8" '
                f'fill="{BOX_FILL}" stroke="{ACCENT if key != "acteurs" else INK}" stroke-width="1.2"/>'
            )
            label = _wrap(name, 22)[:2]
            parts.append(_text_block(x + col_w / 2, y + (20 if len(label) > 1 else 26), label, size=12, weight="600"))
            parts.append(_text_block(x + col_w / 2, y + box_h - 7, [item_id], size=10, fill=MUTED))

    return _svg(width, height, "".join(parts), "diagramme-architecture", "Vue de bout en bout du système")


def architecture_mermaid(dossier: ConceptionDossier) -> str:
    model = _architecture_model(dossier)
    if not model:
        return ""
    columns, edges = model

    def node(item_id: str) -> str:
        return item_id.replace("-", "_")

    lines = ["flowchart LR"]
    for key, title in COLUMNS:
        if not columns.get(key):
            continue
        lines.append(f'    subgraph {key}["{_mermaid_label(title)}"]')
        lines += [f'        {node(i)}["{_mermaid_label(name)}"]' for i, name in columns[key]]
        lines.append("    end")
    lines += [f"    {node(src)} --> {node(dst)}" for src, dst in edges]
    return "\n".join(lines)


# --- Flux des opérations d'un cas d'utilisation --------------------------------------------------

METHOD_COLORS = {
    "GET": "#0284c7",
    "POST": "#059669",
    "PUT": "#d97706",
    "PATCH": "#7c3aed",
    "DELETE": "#dc2626",
}
DANGER = "#dc2626"
DANGER_BG = "#fef2f2"
WARN = "#b45309"


def _text_left(x: float, y: float, lines: Sequence[str], size: int = 12, weight: str = "400",
               fill: str = INK, mono: bool = False) -> str:
    family = ' font-family="ui-monospace, SFMono-Regular, Menlo, monospace"' if mono else ""
    tspans = "".join(
        f'<tspan x="{x:.0f}" dy="{0 if i == 0 else size + 5}">{escape(line)}</tspan>' for i, line in enumerate(lines)
    )
    return f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" font-weight="{weight}" fill="{fill}"{family}>{tspans}</text>'


def _operation_rows(op: Operation, entites: Dict[str, str], dossier: Optional[ConceptionDossier] = None) -> List[Tuple[str, str, str]]:
    """Lignes (libellé, valeur, couleur) de la fiche d'une opération."""
    def champ(c: Champ) -> str:
        return c.nom if c.emplacement == "corps" else f"{c.nom} ({c.emplacement})"

    requis = [champ(c) for c in op.champs if c.requis]
    facultatifs = [champ(c) for c in op.champs if not c.requis]
    rows = [
        ("Sécurité", " ou ".join(op.securite) if op.securite else "Non déclarée", INK if op.securite else WARN),
        ("Entrées requises", ", ".join(requis) or "aucune", INK),
    ]
    if facultatifs:
        rows.append(("Facultatives", ", ".join(facultatifs), MUTED))
    if op.effets and dossier is not None:
        from .database import operation_db_effects  # import tardif : database réutilise ce module

        lines = [line for title, details in operation_db_effects(op, dossier) for line in [title, *(f"· {d}" for d in details)]]
        rows.append(("Base de données", "\n".join(lines), INK))
    elif op.stocke is None:
        rows.append(("Stockage", "Stockage non déclaré", WARN))
    elif not op.stocke:
        rows.append(("Stockage", "Rien n'est stocké", INK))
    else:
        rows.append(("Stockage", ", ".join(f"{entites.get(e, e)} ({e})" if e in entites else e for e in op.stocke), INK))
    return rows


def _flow_model(uc: CasUtilisation, dossier: ConceptionDossier):
    if not uc.endpoints:
        return None
    ops = {op.operation_id: op for op in dossier.operations}
    entites = {e.id: e.nom for e in (dossier.architecture.entites if dossier.architecture else []) if e.nom}
    acteurs = {a.id: a.nom for a in (dossier.exigences.acteurs if dossier.exigences else [])}
    debut = acteurs.get(uc.acteur_principal) or uc.acteur_principal or "Début"
    fin = "; ".join(p for p in uc.postconditions if p.strip()) or "Fin du cas d'utilisation"
    steps = [(ep, ops.get(ep)) for ep in uc.endpoints if ep.strip()]
    return debut, steps, fin, entites


def _wrap_lines(value: str, width: int) -> List[str]:
    return [line for part in value.split("\n") for line in _wrap(part, width)]


def api_flow_svg(uc: CasUtilisation, dossier: ConceptionDossier) -> str:
    """Enchaînement des appels d'API d'un cas d'utilisation : fiche de chaque appel, branches d'échec, suite."""
    model = _flow_model(uc, dossier)
    if not model:
        return ""
    debut, steps, fin, entites = model

    card_x, card_w, err_x, err_w, gap = 20, 460, 530, 270, 46
    width = err_x + err_w + 20
    cx = card_x + card_w / 2
    parts: List[str] = []

    def pill(y: float, label: str, fill: str) -> float:
        lines = _wrap(label, 60)
        h = 14 + 16 * len(lines)
        parts.append(f'<rect x="{cx - 200:.0f}" y="{y:.0f}" width="400" height="{h}" rx="{h / 2:.0f}" fill="{fill}"/>')
        parts.append(_text_block(cx, y + 19, lines, size=12, weight="600", fill="#ffffff"))
        return h

    def arrow(y1: float, y2: float, label: str = "") -> None:
        parts.append(f'<path d="M{cx:.0f},{y1:.0f} L{cx:.0f},{y2 - 2:.0f}" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#fleche)"/>')
        if label:
            parts.append(_text_left(cx + 8, (y1 + y2) / 2 + 4, [label], size=11, weight="600", fill="#059669"))

    y = 16.0
    y += pill(y, f"Déclencheur : {debut}", INK)

    for i, (op_id, op) in enumerate(steps):
        top = y + gap
        arrow(y, top, "" if i == 0 else _success_label(steps[i - 1][1]))

        if op is None:
            h = 46
            parts.append(f'<rect x="{card_x}" y="{top:.0f}" width="{card_w}" height="{h}" rx="10" fill="#f8fafc" '
                         f'stroke="{WARN}" stroke-dasharray="5 4"/>')
            parts.append(_text_left(card_x + 16, top + 28, [f"{op_id} : introuvable dans api/openapi.yaml"], weight="600", fill=WARN))
            y = top + h
            continue

        color = METHOD_COLORS.get(op.methode, MUTED)
        rows = [(label, _wrap_lines(value, 46), fill) for label, value, fill in _operation_rows(op, entites, dossier)]
        subtitle = f"{op.operation_id} — {op.resume}" if op.resume else op.operation_id
        h = 30 + 24 + sum(6 + 17 * len(lines) for _, lines, _ in rows) + 8

        parts.append(f'<rect x="{card_x}" y="{top:.0f}" width="{card_w}" height="{h}" rx="10" fill="{BOX_FILL}" stroke="{color}" stroke-width="1.4"/>')
        parts.append(f'<path d="M{card_x},{top + 30:.0f} V{top + 10:.0f} a10,10 0 0 1 10,-10 H{card_x + card_w - 10} '
                     f'a10,10 0 0 1 10,10 V{top + 30:.0f} z" fill="{color}" opacity="0.1"/>')
        parts.append(f'<rect x="{card_x + 10}" y="{top + 7:.0f}" width="{14 + 8 * len(op.methode)}" height="18" rx="4" fill="{color}"/>')
        parts.append(_text_left(card_x + 17, top + 20, [op.methode], size=11, weight="700", fill="#ffffff"))
        parts.append(_text_left(card_x + 32 + 8 * len(op.methode), top + 20, [op.chemin], size=12, weight="600", mono=True))
        sub = _wrap(subtitle, 66)
        parts.append(_text_left(card_x + 16, top + 48, [sub[0] + (" …" if len(sub) > 1 else "")], size=11, fill=MUTED))

        ry = top + 54
        for label, lines, fill in rows:
            ry += 6
            parts.append(_text_left(card_x + 16, ry + 12, [label], size=11, weight="700", fill=MUTED))
            parts.append(_text_left(card_x + 140, ry + 12, lines, size=12, fill=fill))
            ry += 17 * len(lines)

        if op.erreurs:
            err_lines = [line for r in op.erreurs for line in _wrap(f"{r.code} — {r.description or 'Erreur'}", 38)]
            eh = 30 + 17 * len(err_lines)
            ey = top
            parts.append(f'<path d="M{card_x + card_w},{top + 18:.0f} L{err_x - 2},{ey + 18:.0f}" stroke="{DANGER}" '
                         f'stroke-width="1.3" stroke-dasharray="5 4" marker-end="url(#fleche)"/>')
            parts.append(f'<rect x="{err_x}" y="{ey:.0f}" width="{err_w}" height="{eh}" rx="10" fill="{DANGER_BG}" stroke="{DANGER}"/>')
            parts.append(_text_left(err_x + 14, ey + 19, ["Si échec"], size=11, weight="700", fill=DANGER))
            parts.append(_text_left(err_x + 14, ey + 38, err_lines, size=12, fill=INK))
            h = max(h, eh)
        y = top + h

    last = steps[-1][1] if steps else None
    end_top = y + gap
    arrow(y, end_top, _success_label(last))
    y = end_top + pill(end_top, f"Fin : {fin}", ACCENT)

    return _svg(width, y + 16, "".join(parts), "diagramme-flux", f"Flux des opérations — {uc.id} {uc.nom}")


def _success_label(op: Optional[Operation]) -> str:
    if not op or not op.succes:
        return ""
    first = op.succes[0]
    return f"{first.code} {first.description}".strip()


def api_flow_mermaid(uc: CasUtilisation, dossier: ConceptionDossier) -> str:
    model = _flow_model(uc, dossier)
    if not model:
        return ""
    debut, steps, fin, entites = model

    lines = ["flowchart TD", f'    D(["{_mermaid_label("Déclencheur : " + debut)}"])']
    previous, previous_op = "D", None
    for i, (op_id, op) in enumerate(steps, start=1):
        node = f"O{i}"
        if op is None:
            lines.append(f'    {node}["{_mermaid_label(op_id + " : introuvable dans api/openapi.yaml")}"]')
        else:
            label = [f"{op.methode} {op.chemin}", op.operation_id]
            label += [f"{name} : {value}" for name, value, _ in _operation_rows(op, entites, dossier)]
            parts = [line for part in label for line in part.split("\n")]
            lines.append(f'    {node}["{"<br/>".join(_mermaid_label(part) for part in parts)}"]')
            if op.erreurs:
                errors = ["Si échec"] + [f"{r.code} {r.description}".strip() for r in op.erreurs]
                lines.append(f'    E{i}["{"<br/>".join(_mermaid_label(part) for part in errors)}"]')
                lines.append(f"    {node} -.-> E{i}")
        success = _success_label(previous_op)
        lines.append(f'    {previous} -- "{_mermaid_label(success)}" --> {node}' if success else f"    {previous} --> {node}")
        previous, previous_op = node, op
    success = _success_label(previous_op)
    lines.append(f'    F(["{_mermaid_label("Fin : " + fin)}"])')
    lines.append(f'    {previous} -- "{_mermaid_label(success)}" --> F' if success else f"    {previous} --> F")
    return "\n".join(lines)
