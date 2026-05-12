from __future__ import annotations

from typing import Sequence


def calculate_ndmi_values(nir_values: Sequence[float], swir_values: Sequence[float], nodata: float = -9999.0) -> list[float]:
    if len(nir_values) != len(swir_values):
        raise ValueError("nir_values and swir_values must have the same length")

    output: list[float] = []
    for nir, swir in zip(nir_values, swir_values):
        denominator = float(nir) + float(swir)
        if denominator == 0.0:
            output.append(nodata)
            continue
        value = (float(nir) - float(swir)) / denominator
        output.append(round(value, 6))
    return output
