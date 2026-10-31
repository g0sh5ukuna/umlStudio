"""Reporters console, HTML, Markdown et Spécifications Développeur pour umlStudio."""

from .console import (
    print_banner,
    render_rules_report,
    render_matrix_report,
    render_stats_dashboard,
)
from .matrix import TraceabilityReport, build_traceability_matrix
from .html import generate_html_report
from .markdown import generate_markdown_report
from .spec_doc import generate_spec_markdown, generate_spec_html

__all__ = [
    "print_banner",
    "render_rules_report",
    "render_matrix_report",
    "render_stats_dashboard",
    "TraceabilityReport",
    "build_traceability_matrix",
    "generate_html_report",
    "generate_markdown_report",
    "generate_spec_markdown",
    "generate_spec_html",
]
