# backend/core/dependency_injector.py
# Inyección de dependencias para agentes CASTÚO-SYSTEM™ v2.0

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, Type

logger = logging.getLogger(__name__)


class DependencyInjector:
    """
    Contenedor de dependencias para agentes.
    - Registro de instancias y factories.
    - Resolución por nombre.
    - Creación de instancias con dependencias inyectadas vía anotaciones de __init__.
    """

    def __init__(self) -> None:
        self.container: Dict[str, Any] = {}
        self.factories: Dict[str, Callable[[], Any]] = {}

    def register(self, name: str, instance: Any, singleton: bool = True) -> None:
        self.container[name] = instance
        if not singleton:
            logger.warning("Non-singleton registration for %s is not fully supported yet.", name)

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        self.factories[name] = factory

    def resolve(self, name: str) -> Any:
        if name in self.container:
            return self.container[name]
        if name in self.factories:
            instance = self.factories[name]()
            if name not in self.container:
                self.container[name] = instance
            return instance
        raise ValueError(f"Dependency {name} not registered.")

    def inject(self, cls: Type[Any]) -> Any:
        """
        Crea una instancia de la clase inyectando dependencias.
        Las dependencias se resuelven por anotación de tipo (nombre del tipo) o por nombre de parámetro.
        """
        sig = inspect.signature(cls.__init__)
        dependencies: Dict[str, Any] = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param.annotation is inspect.Parameter.empty:
                continue
            type_name = getattr(param.annotation, "__name__", None) or str(param.annotation)
            if "Optional" in type_name or "Union" in type_name:
                try:
                    from typing import get_args, get_origin
                    args = get_args(param.annotation)
                    type_name = next((getattr(a, "__name__", str(a)) for a in args if a is not type(None)), type_name)
                except Exception:
                    pass
            if type_name in self.container or type_name in self.factories:
                try:
                    dependencies[param_name] = self.resolve(type_name)
                except ValueError:
                    pass
            elif param_name.replace("_agent", "").replace("_", "") in ("selfhealing", "ecommerce", "logistics", "compliance", "ai"):
                reg_name = {"selfhealing_agent": "SelfHealingAgent", "ecommerce_agent": "ECommerceAgent", "logistics_agent": "LogisticsAgent", "compliance_agent": "ComplianceAgent", "ai_agent": "TunedAIAgent"}.get(param_name)
                if reg_name and (reg_name in self.container or reg_name in self.factories):
                    try:
                        dependencies[param_name] = self.resolve(reg_name)
                    except ValueError:
                        pass

        return cls(**dependencies)

    def clear(self) -> None:
        self.container.clear()
        self.factories.clear()


injector = DependencyInjector()
