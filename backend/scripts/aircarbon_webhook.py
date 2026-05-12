#!/usr/bin/env python3
"""
Servidor Flask para recibir webhooks de AirCarbon Exchange.
Al completarse una venta (credit_sale_completed), opcionalmente registrar en GaiaChain.
Ejemplo: python3 scripts/aircarbon_webhook.py  # Escucha en puerto 5000
"""
import os
import subprocess
import sys

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    print("Webhook recibido:", data)

    if data.get("event") == "credit_sale_completed":
        farm_id = data.get("farm_id", "farm-eu-001")
        kg_co2 = data.get("amount_kg", 0)
        verra_project_id = data.get("verra_project_id", "")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "scripts/tokenize_crop.py",
                    farm_id,
                    "lettuce",
                    "288",
                    str(int(kg_co2)),
                    verra_project_id,
                ],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                check=False,
                capture_output=True,
            )
        except Exception as e:
            print("Error tokenizando:", e)

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
