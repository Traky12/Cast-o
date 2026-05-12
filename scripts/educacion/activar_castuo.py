# -*- coding: utf-8 -*-
"""
ACTIVAR CASTÚO: script para "activar" el NFT de Castúo al final del juego del mapa del tesoro.
Muestra mensaje de victoria, datos del NFT (simulados) y un mini-juego de preguntas.
Requisitos: Python 3.x (sin dependencias extra).
Uso: python scripts/educacion/activar_castuo.py
"""
from __future__ import annotations

import sys
import time

NFT_DATA = {
    "nombre": "Castúo-System: El Olivo Cuántico",
    "dueño": "Los Guardianes Cuánticos de la Dehesa",
    "superpoderes": [
        "Conecta 100 fincas con su red de raíces.",
        "Protegido por Sabionda y un escudo de encina cuántica.",
        "Certificado por la UE (incluso Bruselas lo aprueba).",
        "Ahorra agua como un camello extremeño.",
    ],
    "hash": "a1b2c3... (SHA-256 del ZIP de prueba)",
    "certificado": "SABIONDA-AUTH-V1.cert",
    "libro_secretos": "SABIONDA_FINAL_RELEASE.log",
    "sello": "scripts/seal.py --verify",
    "nft_id": "CASTÚO-GOLD-001-TESTNET",
}


def mostrar_mensaje_victoria() -> None:
    mensaje = """
    ¡LO HABÉIS CONSEGUIDO!

    Castúo está a salvo gracias a vosotros, los nuevos
    Guardianes Cuánticos de la Dehesa.

    Sabionda ha activado el NFT de protección y los
    Jabalíes Digitales han huido.

    ¡Las aceitunas volverán a brillar esta noche!

    --- DATOS DEL NFT ACTIVADO ---
    """
    for linea in mensaje.strip().split("\n"):
        print(linea)
        time.sleep(0.35)
    for clave, valor in NFT_DATA.items():
        if isinstance(valor, list):
            print(f"  {clave.replace('_', ' ').title()}:")
            for item in valor:
                print(f"    - {item}")
        else:
            print(f"  {clave.replace('_', ' ').title()}: {valor}")
        time.sleep(0.2)
    print("\n  Sonad tambores y panderetas!")
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_OK)
    except Exception:
        pass


def juego_preguntas() -> None:
    preguntas = [
        {
            "pregunta": "¿Qué guardaba el Certificado Mágico de Castúo?",
            "opciones": ["A) Recetas de cocina", "B) Las reglas que cumplía Castúo", "C) Chistes de jabalíes"],
            "respuesta": "B",
        },
        {
            "pregunta": "¿Dónde escondimos el Libro de los Secretos?",
            "opciones": ["A) Debajo de las raíces de Castúo", "B) En el frigorífico", "C) En la nube (literalmente)"],
            "respuesta": "A",
        },
        {
            "pregunta": "¿Qué usamos para ahuyentar a los Jabalíes Digitales?",
            "opciones": ["A) Un jamón ibérico", "B) Un tractor pirata", "C) Datos falsos de curación de jamones"],
            "respuesta": "C",
        },
    ]
    print("\n  MINI-JUEGO: Pon a prueba tus conocimientos")
    puntos = 0
    for i, p in enumerate(preguntas, 1):
        print(f"\nPregunta {i}: {p['pregunta']}")
        for op in p["opciones"]:
            print(f"  {op}")
        try:
            respuesta = input("Tu respuesta (A/B/C): ").strip().upper() or " "
        except EOFError:
            respuesta = " "
        if respuesta == p["respuesta"]:
            print("  Correcto. Sabionda está orgullosa.")
            puntos += 1
        else:
            print(f"  Casi... La respuesta era {p['respuesta']}.")
    print(f"\n  RESULTADO: {puntos}/3 aciertos.")
    if puntos == 3:
        print("  Eres un MAESTRO CUÁNTICO. Castúo te nombra Guardián Honorífico.")
    elif puntos >= 1:
        print("  Buen trabajo; aún hay más por aprender.")
    else:
        print("  Los Jabalíes se han reído... Pero no te rindas.")


def mensaje_despedida() -> None:
    print("\n  FIN DE LA AVENTURA (por ahora)")
    print("""
  ¿Qué quieres hacer ahora?
  1) Volver a verificar el NFT de Castúo
  2) Dibujar tu propio olivo cuántico
  3) Ver el simulador de sensor de Castúo (sensor_castuo.py)
  4) Salir y explorar la finca de verdad
    """)
    try:
        opcion = input("Elige un número (1-4): ").strip() or "4"
    except EOFError:
        opcion = "4"
    if opcion == "1":
        mostrar_mensaje_victoria()
    elif opcion == "2":
        print("\n  IDEAS PARA DIBUJAR:")
        print("  - Un olivo con paneles solares en las hojas.")
        print("  - Sabionda como una aceituna con gafas.")
        print("  - Los Jabalíes Digitales huyendo de un jamón gigante.")
    elif opcion == "3":
        print("\n  Ejecuta: python scripts/educacion/sensor_castuo.py")
        print("  para ver cómo Castúo mide la humedad del suelo.")
    else:
        print("\n  Que la fuerza cuántica te acompañe, explorador.\n")


def main() -> int:
    print("""
  ACTIVACIÓN DEL NFT DE CASTÚO
  ----------------------------
  Has recuperado todos los tesoros.
  Vamos a activar el NFT que protegerá a Castúo.
    """)
    try:
        input("Presiona ENTER para continuar...")
    except EOFError:
        pass
    mostrar_mensaje_victoria()
    try:
        input("\nPresiona ENTER para el mini-juego de preguntas...")
    except EOFError:
        pass
    juego_preguntas()
    mensaje_despedida()
    return 0


if __name__ == "__main__":
    sys.exit(main())
