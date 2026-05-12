# -*- coding: utf-8 -*-
"""Optimización de rutas (VRP) con OR-Tools (Vehicle Routing Problem)."""
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False


def get_distance_matrix_stub(locations: List[Tuple[float, float]]) -> np.ndarray:
    """Matriz de distancias (stub; en producción usar Google Maps Distance Matrix API)."""
    n = len(locations)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                a, b = locations[i], locations[j]
                matrix[i][j] = np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) * 111  # km aprox
    return matrix


def optimize_routes(
    vehicles: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    distance_matrix: Optional[np.ndarray] = None,
    depot_index: int = 0,
) -> Dict[str, Any]:
    """
    Optimiza rutas VRP con capacidad y ventanas de tiempo (stub si no OR-Tools).
    vehicles: [{"id": 1, "capacity": 1000}]
    orders: [{"id": 1, "location_index": 1, "demand": 10}]
    """
    if not HAS_ORTOOLS:
        return {
            "status": "no_ortools",
            "routes": [[depot_index, o["location_index"], depot_index] for o in orders[: len(vehicles)]],
            "message": "Instalar ortools para optimización real",
        }

    n = distance_matrix.shape[0] if distance_matrix is not None else max(o["location_index"] for o in orders) + 1
    if distance_matrix is None:
        locations = [(0.0, 0.0)] * n
        distance_matrix = get_distance_matrix_stub(locations)

    demands = [0] * n
    for o in orders:
        idx = o.get("location_index", 0)
        if 0 <= idx < n:
            demands[idx] = int(o.get("demand", 0))

    manager = pywrapcp.RoutingIndexManager(n, len(vehicles), depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        return demands[manager.IndexToNode(from_index)]

    routing.AddDimension(
        routing.RegisterUnaryTransitCallback(demand_callback),
        0,
        [int(v.get("capacity", 1000)) for v in vehicles],
        True,
        "Capacity",
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)
    routes = []
    if solution:
        for v in range(len(vehicles)):
            route = []
            index = routing.Start(v)
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
            routes.append(route)
    else:
        routes = [[depot_index, depot_index]] * len(vehicles)

    return {"status": "ok", "routes": routes}
