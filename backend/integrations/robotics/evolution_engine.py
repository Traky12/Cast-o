from __future__ import annotations

import hashlib
import json
import random
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Population = List[List[float]]


def evolve_simple_genetic(
    population_size: int = 32,
    genes: int = 10,
    generations: int = 8,
    rng: Optional[random.Random] = None,
    fitness: Optional[Callable[[List[float]], float]] = None,
) -> Dict[str, Any]:
    """
    Motor evolutivo mínimo sin dependencias extra; fitness por defecto = suma (sustituir por métrica de tarea real).
    """
    r = rng or random.Random()
    fit = fitness or (lambda ind: float(sum(ind)))

    population: Population = [[r.random() for _ in range(genes)] for _ in range(population_size)]

    logbook: List[Dict[str, float]] = []
    for _ in range(generations):
        scored = [(fit(ind), ind) for ind in population]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_f = scored[0][0]
        avg_f = sum(s for s, _ in scored) / len(scored)
        logbook.append({"best": best_f, "avg": avg_f})

        elite_n = max(2, population_size // 4)
        elites = [ind for _, ind in scored[:elite_n]]
        next_gen: Population = list(elites)
        while len(next_gen) < population_size:
            a, b = r.sample(elites, 2)
            cut = r.randrange(1, genes)
            child = a[:cut] + b[cut:]
            if r.random() < 0.25:
                idx = r.randrange(genes)
                child[idx] = max(0.0, min(1.0, child[idx] + r.gauss(0, 0.15)))
            next_gen.append(child)
        population = next_gen

    best_ind = max(population, key=fit)
    return {
        "best_individual": best_ind,
        "fitness": fit(best_ind),
        "logbook": logbook,
        "genes": genes,
        "generations": generations,
    }


def _state_fingerprint(individual: Sequence[float], generation: int) -> str:
    payload = json.dumps({"g": generation, "v": list(individual)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EvolutionEngine:
    """Fachada: GA simple integrado; rama DEAP opcional si está instalada."""

    def __init__(self, population_size: int = 32) -> None:
        self.population_size = population_size

    def evolve(self, generations: int = 8, genes: int = 10) -> Dict[str, Any]:
        return evolve_simple_genetic(
            population_size=self.population_size,
            genes=genes,
            generations=generations,
        )

    def evolve_with_deap(
        self,
        generations: int = 8,
        genes: int = 10,
    ) -> Dict[str, Any]:
        try:
            from deap import algorithms, base, creator, tools  # type: ignore
        except ImportError as e:
            raise ImportError("Instala DEAP (requirements-optional) o usa evolve().") from e

        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("attr_float", random.random)
        toolbox.register(
            "individual",
            tools.initRepeat,
            creator.Individual,
            toolbox.attr_float,
            n=genes,
        )
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", tools.cxBlend, alpha=0.5)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)

        def evaluate(ind: List[float]) -> Tuple[float]:
            return (float(sum(ind)),)

        toolbox.register("evaluate", evaluate)

        population = toolbox.population(n=self.population_size)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", lambda x: sum(x) / len(x) if x else 0.0)
        stats.register("min", min)
        stats.register("max", max)

        population, logbook = algorithms.eaSimple(
            population,
            toolbox,
            cxpb=0.5,
            mutpb=0.2,
            ngen=generations,
            stats=stats,
            verbose=False,
        )
        best = tools.selBest(population, k=1)[0]
        return {
            "best_individual": list(best),
            "fitness": float(best.fitness.values[0]),
            "logbook": logbook,
            "genes": genes,
            "generations": generations,
            "engine": "deap",
        }

    def save_checkpoint(
        self,
        state: Dict[str, Any],
        path: str,
        robot_id: str,
    ) -> str:
        """Persistencia local; la cadena se ancla vía build_robot_evolution_audit_payload + register_event_in_chain."""
        digest = _state_fingerprint(state["best_individual"], int(state.get("generations", 0)))
        record = {
            "robot_id": robot_id,
            "digest_sha256": digest,
            "best_individual": state["best_individual"],
            "fitness": state.get("fitness"),
            "saved_utc": time.time(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        return digest
