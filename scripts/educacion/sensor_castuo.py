# -*- coding: utf-8 -*-
"""
Simulador de sensor de humedad de Castúo.
Muestra lecturas simuladas como si el olivo midiera el agua del suelo.
Uso: python scripts/educacion/sensor_castuo.py
"""
from __future__ import annotations

import random
import time

def main() -> None:
    print("Simulador de sensor de humedad de Castúo\n")
    for i in range(5):
        humedad = random.randint(20, 100)
        estado = "Óptimo" if humedad > 50 else "Riega ya!"
        print(f"  Humedad del suelo: {humedad}% | Estado: {estado}")
        time.sleep(1)
    print("\n  Fin del simulador. Castúo sigue vigilando.")


if __name__ == "__main__":
    main()
