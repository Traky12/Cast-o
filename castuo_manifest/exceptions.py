"""Violaciones de integridad del manifiesto soberano."""


class SovereigntyViolationError(RuntimeError):
    """
    Unidad atómica V1.0-SOVEREIGNTY: no se exportan componentes del manifiesto
    sin el bloque eu_sovereignty validado.
    """

    pass
