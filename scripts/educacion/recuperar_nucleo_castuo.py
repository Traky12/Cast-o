# -*- coding: utf-8 -*-
"""
MISIÓN: RECUPERAR EL NÚCLEO DE CASTÚO
Simula el "hackeo" del núcleo de Castúo en la sala de servidores de AgroTech.
Comandos: infectar, copiar (x5), escapar. Gana antes de que se acabe el tiempo.
Uso: python scripts/educacion/recuperar_nucleo_castuo.py
"""
from __future__ import annotations

import random
import sys


def mostrar_intro() -> None:
    print("""
  MISIÓN: RECUPERAR EL NÚCLEO DE CASTÚO
  --------------------------------------
  Estás dentro de la sala de servidores de AgroTech.
  Tienes 10 minutos para:
  1. Engañar al sistema (virus COBOL).
  2. Copiar los 5 paquetes de datos del núcleo.
  3. Escapar antes de que los guardias lleguen.

  ADVERTENCIA: Si te atrapan, el núcleo se borrará.
    """)
    try:
        input("Presiona ENTER para comenzar...")
    except EOFError:
        pass


def hackear_sistema() -> bool:
    tiempo_restante = 600
    datos_copiados = 0
    total_datos = 5

    print("\n  CONSOLA DE HACKEO (escribe 'ayuda' para ver comandos)")
    while tiempo_restante > 0 and datos_copiados < total_datos:
        minutos = tiempo_restante // 60
        segundos = tiempo_restante % 60
        print(f"\n  Tiempo restante: {minutos:02d}:{segundos:02d}")
        try:
            comando = input("\n> ").lower().strip()
        except EOFError:
            comando = ""

        if comando == "ayuda":
            print("""
  COMANDOS:
  - infectar: Activa el virus COBOL (el sistema cree que es 1995).
  - copiar:   Copia un paquete del núcleo (hazlo 5 veces).
  - escapar:  Salir (solo si has copiado todo).
  - estado:   Ver progreso.
            """)
        elif comando == "infectar":
            print("  Virus COBOL activado. El sistema cree que es 1995.")
            print("  Acceso a servidores: OK. Firewall desactivado: OK.")
            tiempo_restante -= 30
        elif comando == "copiar":
            datos_copiados += 1
            print(f"  Paquete {datos_copiados}/{total_datos} copiado.")
            if datos_copiados == total_datos:
                print("  Todos los datos recuperados.")
        elif comando == "estado":
            print(f"  ESTADO: {datos_copiados}/{total_datos} paquetes copiados.")
        elif comando == "escapar":
            if datos_copiados == total_datos:
                print("  Escapando con el núcleo. Los guardias no te atraparán.")
                print("  MISIÓN COMPLETADA: Castúo está a salvo.")
                return True
            print("  No puedes escapar sin todos los datos.")
        else:
            print("  Comando desconocido. Escribe 'ayuda'.")

        tiempo_restante -= 5
        if random.random() < 0.1:
            print("  ALERTA: Los guardias están cerca. Date prisa.")

    if tiempo_restante <= 0:
        print("  TIEMPO AGOTADO. Los guardias te han atrapado.")
        print("  El núcleo de Castúo se ha borrado... Game Over.")
        return False
    return True


def main() -> int:
    mostrar_intro()
    exito = hackear_sistema()
    if exito:
        print("""
  EPÍLOGO: UN AÑO DESPUÉS
  Gracias a ti, el núcleo de Castúo fue liberado.
  Cualquier agricultor puede acceder a los datos climáticos sin pagar.
  Las corporaciones perdieron el control. La lucha continúa.

  ¿Te unirás a la Alianza de los Datos Verdes?
        """)
    return 0 if exito else 1


if __name__ == "__main__":
    sys.exit(main())
