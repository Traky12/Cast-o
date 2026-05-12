from pkgutil import extend_path

# Permite que `services.*` resuelva submódulos tanto desde `api/services`
# como desde `services/` en la raíz del repositorio.
__path__ = extend_path(__path__, __name__)
