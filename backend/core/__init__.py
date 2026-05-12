# backend/core — Núcleo compartido (inyección de dependencias, etc.)

try:
    from backend.core.dependency_injector import DependencyInjector, injector
except ImportError:
    from .dependency_injector import DependencyInjector, injector

__all__ = ["DependencyInjector", "injector"]
