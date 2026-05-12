# -*- coding: utf-8 -*-
"""
Gestor de dependencias entre módulos para carga ordenada.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set

from core.profile_engine import ProfileType
from core.module_loader import ModuleLoader


class DependencyManager:
    """Gestor de dependencias entre módulos para carga ordenada."""

    def __init__(self, module_loader: Optional[ModuleLoader] = None) -> None:
        self.module_loader = module_loader or ModuleLoader()
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        for name, info in self.module_loader.available_modules.items():
            for dep in info.get("dependencies", []):
                self.dependency_graph[name].add(dep)

    def get_load_order(self, module_names: List[str]) -> Optional[List[str]]:
        """Determina el orden de carga para evitar conflictos de dependencias."""
        visited: Set[str] = set()
        load_order: List[str] = []
        temp_visited: Set[str] = set()

        def visit(module: str) -> None:
            if module in temp_visited:
                raise ValueError(f"Dependencia circular detectada: {module}")
            if module in visited:
                return
            temp_visited.add(module)
            for dep in self.dependency_graph.get(module, set()):
                visit(dep)
            temp_visited.discard(module)
            visited.add(module)
            load_order.append(module)

        try:
            for module in module_names:
                if module not in visited:
                    visit(module)
            return load_order
        except ValueError:
            return None

    def load_modules_with_dependencies(
        self,
        module_names: List[str],
        profile_type: ProfileType,
    ) -> Dict[str, object]:
        """Carga módulos y sus dependencias en el orden correcto."""
        load_order = self.get_load_order(module_names)
        if not load_order:
            return {}
        loaded: Dict[str, object] = {}
        for module_name in load_order:
            mod = self.module_loader.load_module(module_name, profile_type)
            if mod is not None:
                loaded[module_name] = mod
        return loaded

    def check_dependencies(self, module_name: str) -> Dict[str, object]:
        """Verifica las dependencias de un módulo."""
        return {
            "module": module_name,
            "direct_dependencies": list(self.dependency_graph.get(module_name, set())),
            "all_dependencies": list(self._get_all_dependencies(module_name)),
        }

    def _get_all_dependencies(self, module_name: str) -> Set[str]:
        """Obtiene todas las dependencias transitivas de un módulo."""
        visited: Set[str] = set()
        stack = [module_name]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for dep in self.dependency_graph.get(current, set()):
                if dep not in visited:
                    stack.append(dep)
        visited.discard(module_name)
        return visited


if __name__ == "__main__":
    dm = DependencyManager()
    print("Dependencias de analytics:", dm.check_dependencies("analytics"))
    order = dm.get_load_order(["analytics", "messaging", "production"])
    print("Orden de carga:", order)
    loaded = dm.load_modules_with_dependencies(["production", "blockchain"], ProfileType.LANDUM_PRO)
    print("Cargados:", list(loaded.keys()))
