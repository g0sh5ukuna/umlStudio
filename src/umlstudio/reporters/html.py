"""Générateur de rapport exécutif HTML ultra-professionnel et autonome."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from jinja2 import Environment

from ..core.rules import RuleResult
from ..models.dossier import ConceptionDossier
from .matrix import TraceabilityReport, build_traceability_matrix

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dossier de Conception - {{ project_name }} ({{ project_code }})</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4f46e5;
            --primary-light: #818cf8;
            --primary-bg: #eef2ff;
            --success: #10b981;
            --success-bg: #ecfdf5;
            --warning: #f59e0b;
            --warning-bg: #fffbeb;
            --danger: #ef4444;
            --danger-bg: #fef2f2;
            --dark: #0f172a;
            --slate-800: #1e293b;
            --slate-600: #475569;
            --slate-400: #94a3b8;
            --slate-200: #e2e8f0;
            --slate-100: #f1f5f9;
            --slate-50: #f8fafc;
            --white: #ffffff;
            --font: 'Plus Jakarta Sans', system-ui, sans-serif;
            --mono: 'JetBrains Mono', monospace;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: var(--font);
            background: #f8fafc;
            color: var(--dark);
            line-height: 1.6;
            padding: 32px 16px;
        }
        .container { max-width: 1200px; margin: 0 auto; }

        /* Header */
        .header {
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
            color: var(--white);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
            margin-bottom: 32px;
            position: relative;
            overflow: hidden;
        }
        .header h1 { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 8px; }
        .header .subtitle { font-size: 1.1rem; opacity: 0.9; font-weight: 400; max-width: 750px; }
        .meta-pills { display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }
        .meta-pill {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* KPI Grid */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 32px; }
        .kpi-card {
            background: var(--white);
            padding: 24px;
            border-radius: 16px;
            border: 1px solid var(--slate-200);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        .kpi-card .label { font-size: 0.85rem; color: var(--slate-600); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        .kpi-card .value { font-size: 2.2rem; font-weight: 800; margin-top: 6px; color: var(--dark); }
        .kpi-card .subtext { font-size: 0.85rem; color: var(--slate-400); margin-top: 4px; }

        /* Section Cards */
        .section-card {
            background: var(--white);
            padding: 32px;
            border-radius: 16px;
            border: 1px solid var(--slate-200);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 32px;
        }
        .section-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--slate-100);
        }

        /* Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.92rem; }
        th {
            background: var(--slate-50);
            padding: 12px 16px;
            text-align: left;
            font-weight: 700;
            color: var(--slate-600);
            border-bottom: 2px solid var(--slate-200);
            font-size: 0.82rem;
            text-transform: uppercase;
        }
        td { padding: 12px 16px; border-bottom: 1px solid var(--slate-200); vertical-align: top; }
        tr:hover td { background: var(--slate-50); }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .badge-success { background: var(--success-bg); color: var(--success); }
        .badge-warning { background: var(--warning-bg); color: var(--warning); }
        .badge-danger { background: var(--danger-bg); color: var(--danger); }
        .badge-primary { background: var(--primary-bg); color: var(--primary); }
        .badge-must { background: #fee2e2; color: #dc2626; }
        .badge-should { background: #fef3c7; color: #d97706; }
        .badge-could { background: #e0e7ff; color: #4338ca; }

        .code-tag {
            font-family: var(--mono);
            background: var(--slate-100);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.82rem;
            color: var(--slate-800);
        }

        /* Violations Box */
        .violation-item {
            background: var(--danger-bg);
            border-left: 4px solid var(--danger);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 12px;
        }
        .violation-title { font-weight: 700; color: #991b1b; font-size: 0.95rem; }
        .violation-action { margin-top: 6px; font-size: 0.85rem; color: #7f1d1d; }

        @media print {
            body { background: white; padding: 0; }
            .section-card { box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }
            .header { background: #1e1b4b !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>{{ project_name }}</h1>
            <p class="subtitle">{{ context or "Dossier de conception d'architecture logicielle" }}</p>
            <div class="meta-pills">
                <span class="meta-pill">Code : {{ project_code }}</span>
                <span class="meta-pill">Commanditaire : {{ commanditaire }}</span>
                <span class="meta-pill">Date : {{ generated_at }}</span>
                <span class="meta-pill">umlStudio v{{ version }}</span>
            </div>
        </header>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="label">Score de Maturité</div>
                <div class="value" style="color: {{ score_color }};">{{ readiness_score }}%</div>
                <div class="subtext">{{ score_message }}</div>
            </div>
            <div class="kpi-card">
                <div class="label">Couverture des Exigences</div>
                <div class="value">{{ matrix.coverage_tests_pct }}%</div>
                <div class="subtext">{{ matrix.tested_exigences }} / {{ matrix.total_exigences }} testées</div>
            </div>
            <div class="kpi-card">
                <div class="label">Couverture des Cas d'Usage</div>
                <div class="value">{{ matrix.coverage_ucs_pct }}%</div>
                <div class="subtext">{{ matrix.covered_ucs }} / {{ matrix.total_ucs }} avec composants</div>
            </div>
            <div class="kpi-card">
                <div class="label">Risques & Conformité</div>
                <div class="value">{{ risks_count }} / {{ dp_count }}</div>
                <div class="subtext">{{ risks_count }} risques | {{ dp_count }} fiches RGPD</div>
            </div>
        </div>

        <!-- Section 1: Contrôle des 10 Règles -->
        <section class="section-card">
            <h2 class="section-title">
                Contrôle des 10 Règles Fondamentales & Intégrité
                <span class="badge badge-primary">{{ passed_rules_count }} / {{ total_rules_count }} Validées</span>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 100px;">Règle</th>
                        <th>Intitulé</th>
                        <th style="width: 120px;">Statut</th>
                        <th>Diagnostic</th>
                    </tr>
                </thead>
                <tbody>
                    {% for r in rules %}
                    <tr>
                        <td><span class="code-tag">{{ r.rule_id }}</span></td>
                        <td><strong>{{ r.title }}</strong></td>
                        <td>
                            {% if r.passed %}
                            <span class="badge badge-success">PASS</span>
                            {% elif r.severity == 'WARNING' %}
                            <span class="badge badge-warning">WARN</span>
                            {% elif r.severity == 'INFO' %}
                            <span class="badge badge-primary">INFO</span>
                            {% else %}
                            <span class="badge badge-danger">FAIL</span>
                            {% endif %}
                        </td>
                        <td>{{ r.summary }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

            {% if violations %}
            <div style="margin-top: 24px;">
                <h3 style="font-size: 1.1rem; color: #991b1b; margin-bottom: 12px;">Points à corriger avant validation formelle :</h3>
                {% for v in violations %}
                <div class="violation-item">
                    <div class="violation-title">[{{ v.file_name }}] {% if v.item_id %}<span class="code-tag">{{ v.item_id }}</span>{% endif %} {{ v.message }}</div>
                    {% if v.recommendation %}
                    <div class="violation-action">➜ Action : {{ v.recommendation }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </section>

        <!-- Section 2: Matrice de Traçabilité de Bout en Bout -->
        <section class="section-card">
            <h2 class="section-title">
                Matrice de Traçabilité de Bout en Bout
                <span class="badge badge-primary">Traçabilité complète</span>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th>Obj.</th>
                        <th>Exigence (EX)</th>
                        <th>Prio.</th>
                        <th>Cas d'Usage (UC)</th>
                        <th>Composants (CMP)</th>
                        <th>Tests (TST)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in matrix.rows %}
                    <tr>
                        <td><span class="code-tag">{{ row.objectif_id }}</span></td>
                        <td><strong>{{ row.exigence_id }}</strong><br><small style="color: var(--slate-600)">{{ row.exigence_titre }}</small></td>
                        <td><span class="badge badge-{{ row.exigence_priorite | lower }}">{{ row.exigence_priorite }}</span></td>
                        <td><span class="code-tag">{{ row.cas_utilisation_id }}</span> {{ row.cas_utilisation_nom }}</td>
                        <td>
                            {% for cmp in row.composants_ids %}
                            <span class="code-tag">{{ cmp }}</span>
                            {% else %}
                            <span style="color: var(--danger)">Non rattaché</span>
                            {% endfor %}
                        </td>
                        <td>
                            {% for tst in row.tests_ids %}
                            <span class="code-tag">{{ tst }}</span>
                            {% else %}
                            <span style="color: var(--danger)">Non testé</span>
                            {% endfor %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>

        <!-- Section 3: Architecture & Décisions -->
        <section class="section-card">
            <h2 class="section-title">Architecture Logicielle & Décisions Structurantes (ADR)</h2>
            {% if architecture and architecture.decisions %}
            <div style="margin-bottom: 24px;">
                <h3 style="margin-bottom: 12px;">Architecture Decision Records (ADR)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Sujet</th>
                            <th>Choix retenu</th>
                            <th>Motivation & Risque</th>
                            <th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for d in architecture.decisions %}
                        <tr>
                            <td><span class="code-tag">{{ d.id }}</span></td>
                            <td><strong>{{ d.sujet }}</strong></td>
                            <td>{{ d.choix }}</td>
                            <td>
                                <div>{{ d.pourquoi }}</div>
                                {% if d.risque_principal %}<small style="color: var(--warning)">Risque : {{ d.risque_principal }}</small>{% endif %}
                            </td>
                            <td><span class="badge badge-primary">{{ d.statut }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}

            {% if architecture and architecture.composants %}
            <h3 style="margin-bottom: 12px;">Composants Applicatifs</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nom</th>
                        <th>Couche</th>
                        <th>Responsabilité</th>
                        <th>Technologie</th>
                    </tr>
                </thead>
                <tbody>
                    {% for c in architecture.composants %}
                    <tr>
                        <td><span class="code-tag">{{ c.id }}</span></td>
                        <td><strong>{{ c.nom }}</strong></td>
                        <td><span class="badge badge-primary">{{ c.couche }}</span></td>
                        <td>{{ c.responsabilite }}</td>
                        <td><span class="code-tag">{{ c.technologie or "-" }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </section>

        <!-- Section 4: Risques & Données Personnelles -->
        <section class="section-card">
            <h2 class="section-title">Gouvernance des Risques & Conformité Données Personnelles</h2>
            {% if risques and risques.risques %}
            <h3 style="margin-bottom: 12px;">Registre des Risques</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Énoncé du Risque</th>
                        <th>Proba / Impact</th>
                        <th>Plan de Mitigation</th>
                        <th>Responsable</th>
                        <th>Statut</th>
                    </tr>
                </thead>
                <tbody>
                    {% for r in risques.risques %}
                    <tr>
                        <td><span class="code-tag">{{ r.id }}</span></td>
                        <td><strong>{{ r.enonce }}</strong></td>
                        <td><span class="badge badge-warning">{{ r.probabilite }} / {{ r.impact }}</span></td>
                        <td>{{ r.mitigation }}</td>
                        <td>{{ r.responsable }}</td>
                        <td><span class="badge badge-primary">{{ r.statut }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if risques and risques.donnees_personnelles %}
            <h3 style="margin-top: 24px; margin-bottom: 12px;">Registre des Données Personnelles (RGPD / APDP)</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Entité</th>
                        <th>Finalité</th>
                        <th>Base Légale</th>
                        <th>Durée Conservation</th>
                    </tr>
                </thead>
                <tbody>
                    {% for dp in risques.donnees_personnelles %}
                    <tr>
                        <td><span class="code-tag">{{ dp.id }}</span></td>
                        <td><span class="code-tag">{{ dp.entite }}</span></td>
                        <td>{{ dp.finalite }}</td>
                        <td><span class="badge badge-primary">{{ dp.base_legale }}</span></td>
                        <td>{{ dp.duree_conservation }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </section>

        <!-- Section 5: Registre des Validations SHA-256 -->
        <section class="section-card">
            <h2 class="section-title">Registre d'Audit & Validations Cryptographiques (SHA-256)</h2>
            {% if validations and validations.validations %}
            <table>
                <thead>
                    <tr>
                        <th>Document</th>
                        <th>Version</th>
                        <th>Empreinte SHA-256</th>
                        <th>Validateur</th>
                        <th>Date</th>
                        <th>Preuve</th>
                    </tr>
                </thead>
                <tbody>
                    {% for v in validations.validations %}
                    <tr>
                        <td><strong>{{ v.document }}</strong></td>
                        <td>{{ v.version }}</td>
                        <td><span class="code-tag">{{ v.sha256[:16] }}...</span></td>
                        <td>{{ v.validateur.nom if v.validateur else "-" }} ({{ v.validateur.role if v.validateur else "" }})</td>
                        <td>{{ v.date or "-" }}</td>
                        <td>{% if v.preuve %}<a href="{{ v.preuve }}" target="_blank">Lien PR</a>{% else %}-{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="color: var(--slate-600); font-style: italic;">Aucune validation formelle enregistrée pour le moment.</p>
            {% endif %}
        </section>

        <footer style="text-align: center; color: var(--slate-400); font-size: 0.85rem; margin-top: 40px;">
            Généré automatiquement par <strong>umlStudio</strong> • Source de vérité des dossiers de conception logicielle
        </footer>
    </div>
</body>
</html>
"""


def generate_html_report(
    dossier: ConceptionDossier,
    rules: List[RuleResult],
    output_path: Path,
) -> None:
    """Génère le rapport exécutif autonome au format HTML."""
    matrix = build_traceability_matrix(dossier)

    # Calcul du score de maturité
    total_rules = len(rules)
    passed_rules = sum(1 for r in rules if r.passed)
    readiness_score = round((passed_rules / total_rules) * 100) if total_rules > 0 else 0

    score_color = "#10b981" if readiness_score >= 90 else ("#f59e0b" if readiness_score >= 60 else "#ef4444")
    score_message = (
        "Dossier conforme et validé"
        if readiness_score == 100
        else ("Dossier en cours de consolidation" if readiness_score >= 60 else "Dossier incomplet (bloquant)")
    )

    all_violations = []
    for r in rules:
        for v in r.violations:
            all_violations.append(v)

    proj_name = (dossier.cadrage.projet.nom if dossier.cadrage and dossier.cadrage.projet else "") or "Projet umlStudio"
    proj_code = (dossier.cadrage.projet.code if dossier.cadrage and dossier.cadrage.projet else "") or "ARCHI"
    commanditaire = (dossier.cadrage.projet.commanditaire.nom if dossier.cadrage and dossier.cadrage.projet and dossier.cadrage.projet.commanditaire else "") or "Direction Projet"
    context_text = (dossier.cadrage.contexte if dossier.cadrage else "") or ""

    template = Environment(autoescape=True).from_string(HTML_TEMPLATE)
    html_content = template.render(
        project_name=proj_name,
        project_code=proj_code,
        commanditaire=commanditaire,
        context=context_text,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        version="0.1.0",
        readiness_score=readiness_score,
        score_color=score_color,
        score_message=score_message,
        matrix=matrix,
        risks_count=len(dossier.risques.risques) if dossier.risques else 0,
        dp_count=len(dossier.risques.donnees_personnelles) if dossier.risques else 0,
        rules=rules,
        total_rules_count=total_rules,
        passed_rules_count=passed_rules,
        violations=all_violations,
        architecture=dossier.architecture,
        risques=dossier.risques,
        validations=dossier.validations,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
