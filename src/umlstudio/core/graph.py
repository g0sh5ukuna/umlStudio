"""Gestion et analyse des graphes de dépendances (Règle 9 : pas de cycles)."""

from typing import Dict, List, Optional, Set, Tuple
from ..models.plan import Lot


class DependencyGraph:
    """Graphe orienté représentant les dépendances entre lots."""

    def __init__(self, lots: List[Lot]):
        self.lots = {lot.id: lot for lot in lots if lot.id}
        # adj[u] = liste des voisins v dont u dépend (u -> v)
        self.adj: Dict[str, List[str]] = {}
        for lot in lots:
            if lot.id:
                self.adj[lot.id] = [dep for dep in lot.depend_de if dep]

    def detect_cycles(self) -> Optional[List[str]]:
        """Détecte s'il y a un cycle dans le graphe.
        Retourne le premier chemin de cycle trouvé (ex: [LOT-01, LOT-02, LOT-01])
        ou None si acyclique (DAG valide).
        """
        # 0 = non visité, 1 = en cours de visite (ancêtre dans la récursion), 2 = terminé
        state: Dict[str, int] = {node: 0 for node in self.adj}
        path: List[str] = []

        def dfs(u: str) -> Optional[List[str]]:
            state[u] = 1
            path.append(u)

            for v in self.adj.get(u, []):
                # Si le nœud cible n'existe même pas dans les lots, on ignore ici (géré par l'intégrité réf)
                if v not in state:
                    continue
                if state[v] == 1:
                    # Cycle détecté ! Trouver où commence le cycle dans path
                    idx = path.index(v)
                    return path[idx:] + [v]
                if state[v] == 0:
                    cycle = dfs(v)
                    if cycle:
                        return cycle

            path.pop()
            state[u] = 2
            return None

        for node in self.adj:
            if state[node] == 0:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

    def topological_sort(self) -> List[str]:
        """Retourne l'ordre d'exécution séquentiel recommandé des lots (du lot sans dépendance aux suivants)."""
        cycle = self.detect_cycles()
        if cycle:
            raise ValueError(f"Impossible de trier topologiquement : cycle détecté ({ ' -> '.join(cycle) })")

        # Calcul des degrés entrants : qui attend qui
        # Si A dépend de B, B doit être fait avant A. Donc dépendance : B -> A
        forward_adj: Dict[str, List[str]] = {node: [] for node in self.adj}
        in_degree: Dict[str, int] = {node: 0 for node in self.adj}

        for u, deps in self.adj.items():
            for v in deps:
                if v in forward_adj:
                    forward_adj[v].append(u)
                    in_degree[u] += 1

        queue = [node for node, deg in in_degree.items() if deg == 0]
        order: List[str] = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for neighbor in forward_adj.get(curr, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order
