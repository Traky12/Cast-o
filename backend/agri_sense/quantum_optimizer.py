"""
Optimizador híbrido QAOA (CASTUO 5.PRO+) — distribución RO / geotermia / ozono.

Restricción de sinergia: x_ro + x_geo + x_o3 <= Perovskita + Biogás (biogrid_5pro).

- Sin Qiskit: enumeración clásica 2^3 (misma lógica de decisión).
- Con qiskit + qiskit_optimization + qiskit_aer: QAOA sobre QUBO binario (Aer).
- CASTUO_IBM_QUANTUM=1 + QISKIT_IBM_TOKEN: intento IBM Runtime (fallback Aer si falla).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from backend.biogrid_5pro import get_bionergy_budget_kw

_LOGGER = logging.getLogger("castuo.quantum_optimizer")

KW_RO_PEAK = 4.2
KW_GEO_PEAK = 3.8
KW_O3_PEAK = 1.5


@dataclass
class QuantumOptimizationResult:
    x_ro_kw: float
    x_geo_kw: float
    x_o3_kw: float
    quantum_confidence_score: float
    backend: str
    objective_value: float
    root_cause_summary: str


def _benefit_ro(ph: float | None, conductivity: float | None) -> float:
    if ph is None:
        return 0.4
    b = 1.0 - abs(ph - 6.2) / 4.0
    if conductivity is not None and conductivity < 1.0:
        b += 0.35
    return max(0.0, min(1.2, b))


def _benefit_geo(ground_temp_c: float | None) -> float:
    if ground_temp_c is None:
        return 0.5
    return max(0.0, 1.0 - abs(ground_temp_c - 18.0) / 12.0)


def _benefit_o3(ph: float | None, ozone_allowed: bool) -> float:
    if not ozone_allowed or ph is None:
        return 0.0
    if ph > 7.2:
        return 0.0
    return 0.45 + 0.2 * (7.2 - ph)


def _classical_optimal_allocation(
    budget_kw: float,
    ph: float | None,
    conductivity_ms_cm: float | None,
    ground_temp_c: float | None,
    ozone_allowed: bool,
) -> tuple[float, float, float, float, str]:
    best_score = -1e9
    best = (0.0, 0.0, 0.0)
    for br in (0, 1):
        for bg in (0, 1):
            for bo in (0, 1):
                e = br * KW_RO_PEAK + bg * KW_GEO_PEAK + bo * KW_O3_PEAK
                if e > budget_kw + 1e-6:
                    continue
                score = (
                    br * _benefit_ro(ph, conductivity_ms_cm) * 2.0
                    + bg * _benefit_geo(ground_temp_c) * 1.8
                    + bo * _benefit_o3(ph, ozone_allowed) * 1.5
                    - 0.08 * e
                )
                if score > best_score:
                    best_score = score
                    best = (br * KW_RO_PEAK, bg * KW_GEO_PEAK, bo * KW_O3_PEAK)
    max_theoretical = 2.4 + 1.8 + 0.97
    q_conf = min(99.9, 72.0 + 27.9 * max(0.0, min(1.0, (best_score + 0.5) / max_theoretical)))
    summary = (
        f"Asignacion BioGrid: RO={best[0]:.2f}kW Geo={best[1]:.2f}kW O3={best[2]:.2f}kW "
        f"techo {budget_kw:.2f}kW (Perovskita+Biogas); salud radicular ponderada."
    )
    return best[0], best[1], best[2], round(q_conf, 2), summary


def _run_qaoa_qiskit(
    budget_kw: float,
    ph: float | None,
    conductivity_ms_cm: float | None,
    ground_temp_c: float | None,
    ozone_allowed: bool,
    use_ibm: bool,
) -> QuantumOptimizationResult | None:
    try:
        from qiskit_algorithms import QAOA
        from qiskit_algorithms.optimizers import COBYLA
        from qiskit.primitives import StatevectorSampler
        from qiskit_optimization import QuadraticProgram
        from qiskit_optimization.algorithms import MinimumEigenOptimizer
    except ImportError:
        return None

    if budget_kw < 0.5:
        return None

    br = _benefit_ro(ph, conductivity_ms_cm)
    bg = _benefit_geo(ground_temp_c)
    bo = _benefit_o3(ph, ozone_allowed)

    qp = QuadraticProgram("biogrid_5pro")
    qp.binary_var(name="b_ro")
    qp.binary_var(name="b_geo")
    qp.binary_var(name="b_o3")
    qp.maximize(linear={"b_ro": br, "b_geo": bg, "b_o3": bo})
    qp.linear_constraint(
        linear={"b_ro": KW_RO_PEAK, "b_geo": KW_GEO_PEAK, "b_o3": KW_O3_PEAK},
        sense="LE",
        rhs=budget_kw,
        name="energy_cap",
    )

    try:
        sampler = StatevectorSampler()
        if use_ibm:
            try:
                from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

                tok = os.getenv("QISKIT_IBM_TOKEN") or os.getenv("IBM_QUANTUM_TOKEN")
                if tok:
                    QiskitRuntimeService.save_account(channel="ibm_quantum", token=tok, overwrite=True)
                    service = QiskitRuntimeService()
                    backend = service.least_busy(operational=True, simulator=False)
                    sampler = SamplerV2(mode=backend)
            except Exception as ex:
                _LOGGER.warning("IBM Quantum fallback a StatevectorSampler: %s", ex)
                sampler = StatevectorSampler()

        qaoa = QAOA(sampler=sampler, optimizer=COBYLA(maxiter=35), reps=2)
        meo = MinimumEigenOptimizer(qaoa)
        sol = meo.solve(qp)
        if sol.x is None:
            return None
        xr = float(sol.x[0]) * KW_RO_PEAK
        xg = float(sol.x[1]) * KW_GEO_PEAK
        xo = float(sol.x[2]) * KW_O3_PEAK
        used = xr + xg + xo
        if used > budget_kw + 0.01:
            xr, xg, xo, qconf, summ = _classical_optimal_allocation(
                budget_kw, ph, conductivity_ms_cm, ground_temp_c, ozone_allowed
            )
            return QuantumOptimizationResult(
                x_ro_kw=xr,
                x_geo_kw=xg,
                x_o3_kw=xo,
                quantum_confidence_score=min(99.0, qconf),
                backend="classical_post_qaoa_feasibility",
                objective_value=float(sol.fval or 0.0),
                root_cause_summary=summ + " (QAOA recortado a techo energetico).",
            )

        prob = 0.88
        if hasattr(sol, "samples") and sol.samples:
            prob = min(1.0, max(0.5, float(sol.samples[0].probability)))

        qconf = min(99.9, 78.0 + 21.0 * prob)
        backend_name = "ibm_quantum" if use_ibm and "SamplerV2" in type(sampler).__name__ else "aer_statevector"
        return QuantumOptimizationResult(
            x_ro_kw=round(xr, 3),
            x_geo_kw=round(xg, 3),
            x_o3_kw=round(xo, 3),
            quantum_confidence_score=round(qconf, 2),
            backend=backend_name,
            objective_value=float(sol.fval or 0.0),
            root_cause_summary=(
                "QAOA (MinimumEigenOptimizer): minima entropia operativa bajo techo Perovskita+Biogas; "
                "punto dulce RO/Geo/O3 para membranas y pH/NPK."
            ),
        )
    except Exception as e:
        _LOGGER.debug("QAOA no ejecutado: %s", e)
        return None


class CastuoQuantumOptimizer:
    """QAOA híbrido para BioGrid 2.0; fallback enumeración clásica."""

    def __init__(self, use_ibm_quantum: bool | None = None) -> None:
        if use_ibm_quantum is None:
            use_ibm_quantum = os.getenv("CASTUO_IBM_QUANTUM", "").lower() in ("1", "true", "yes")
        self.use_ibm_quantum = use_ibm_quantum

    def optimize(
        self,
        irradiance_wm2: float | None,
        *,
        ph: float | None = None,
        conductivity_ms_cm: float | None = None,
        ground_temp_c: float | None = None,
        ozone_injection_allowed: bool = True,
        chlorella_active: bool = True,
    ) -> QuantumOptimizationResult:
        bg = get_bionergy_budget_kw(irradiance_wm2, chlorella_reactor_active=chlorella_active)
        budget = float(bg["total_available_kw"])

        res = _run_qaoa_qiskit(
            budget, ph, conductivity_ms_cm, ground_temp_c, ozone_injection_allowed, self.use_ibm_quantum
        )
        if res is not None:
            return res

        xr, xg, xo, qconf, summary = _classical_optimal_allocation(
            budget, ph, conductivity_ms_cm, ground_temp_c, ozone_injection_allowed
        )
        return QuantumOptimizationResult(
            x_ro_kw=xr,
            x_geo_kw=xg,
            x_o3_kw=xo,
            quantum_confidence_score=qconf,
            backend="classical_enumeration",
            objective_value=0.0,
            root_cause_summary=summary,
        )


def optimize_bionergy_allocation(**kwargs: Any) -> dict[str, Any]:
    opt = CastuoQuantumOptimizer()
    r = opt.optimize(
        kwargs.get("irradiance_wm2"),
        ph=kwargs.get("ph"),
        conductivity_ms_cm=kwargs.get("conductivity_ms_cm"),
        ground_temp_c=kwargs.get("ground_temp_c"),
        ozone_injection_allowed=kwargs.get("ozone_injection_allowed", True),
        chlorella_active=kwargs.get("chlorella_active", True),
    )
    return {
        "x_ro_kw": r.x_ro_kw,
        "x_geo_kw": r.x_geo_kw,
        "x_o3_kw": r.x_o3_kw,
        "quantum_confidence_score": r.quantum_confidence_score,
        "quantum_backend": r.backend,
        "objective_value": r.objective_value,
        "root_cause_summary": r.root_cause_summary,
        "biogrid": get_bionergy_budget_kw(kwargs.get("irradiance_wm2")),
    }
