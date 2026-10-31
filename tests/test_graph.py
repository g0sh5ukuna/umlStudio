"""Tests unitaires pour le moteur de graphe et la détection de cycles (Règle 9)."""

import pytest
from umlstudio.core.graph import DependencyGraph
from umlstudio.models.plan import Lot


def test_acyclic_graph():
    lots = [
        Lot(id="LOT-01", depend_de=[]),
        Lot(id="LOT-02", depend_de=["LOT-01"]),
        Lot(id="LOT-03", depend_de=["LOT-02"]),
    ]
    graph = DependencyGraph(lots)
    cycle = graph.detect_cycles()
    assert cycle is None

    order = graph.topological_sort()
    assert order == ["LOT-01", "LOT-02", "LOT-03"]


def test_cyclic_graph_detection():
    lots = [
        Lot(id="LOT-01", depend_de=["LOT-03"]),
        Lot(id="LOT-02", depend_de=["LOT-01"]),
        Lot(id="LOT-03", depend_de=["LOT-02"]),
    ]
    graph = DependencyGraph(lots)
    cycle = graph.detect_cycles()
    assert cycle is not None
    assert len(cycle) >= 3
    # Le premier et dernier élément du cycle doivent correspondre
    assert cycle[0] == cycle[-1]

    with pytest.raises(ValueError, match="cycle détecté"):
        graph.topological_sort()


def test_independent_lots():
    lots = [
        Lot(id="LOT-01", depend_de=[]),
        Lot(id="LOT-02", depend_de=[]),
    ]
    graph = DependencyGraph(lots)
    assert graph.detect_cycles() is None
    order = graph.topological_sort()
    assert set(order) == {"LOT-01", "LOT-02"}
