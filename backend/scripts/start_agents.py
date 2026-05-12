#!/usr/bin/env python3
# backend/scripts/start_agents.py — Arranque de agentes CASTÚO-SYSTEM™ v2.0 (maestro, selfhealing, ai, ecommerce, logistics, compliance)

import argparse
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

AGENTS = [
    ("master", "backend.agents.master_agent"),
    ("selfhealing", "backend.agents.selfhealing_agent"),
    ("ai", "backend.agents.ai_agent"),
    ("ecommerce", "backend.agents.ecommerce_agent"),
    ("logistics", "backend.agents.logistics_agent"),
    ("compliance", "backend.agents.compliance_agent"),
]


def setup_injector() -> None:
    """Registra dependencias en el inyector para MasterAgent."""
    try:
        from backend.core.dependency_injector import injector
        from backend.agents.selfhealing_agent import SelfHealingAgent
        from backend.agents.ecommerce_agent import ECommerceAgent
        from backend.agents.logistics_agent import LogisticsAgent
        from backend.agents.compliance_agent import ComplianceAgent
        from backend.agents.ai_agent import TunedAIAgent
        injector.register("SelfHealingAgent", SelfHealingAgent())
        injector.register("ECommerceAgent", ECommerceAgent())
        injector.register("LogisticsAgent", LogisticsAgent())
        injector.register("ComplianceAgent", ComplianceAgent())
        injector.register("TunedAIAgent", TunedAIAgent())
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Arrancar agentes CASTÚO-SYSTEM™ v2.0")
    parser.add_argument("agent", nargs="?", choices=[a[0] for a in AGENTS] + ["all"], help="Nombre del agente o 'all'")
    parser.add_argument("--background", "-b", action="store_true", help="Ejecutar en segundo plano (solo Unix)")
    parser.add_argument("--log-dir", default="/var/log/castuo", help="Directorio de logs en modo background")
    args = parser.parse_args()

    agent = args.agent or "all"
    targets = [(n, mod) for n, mod in AGENTS] if agent == "all" else [(n, mod) for n, mod in AGENTS if n == agent]
    if not targets:
        print("Ningún agente seleccionado")
        sys.exit(1)

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", ROOT)
    if ROOT not in env.get("PYTHONPATH", ""):
        env["PYTHONPATH"] = f"{ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"

    setup_injector()
    for name, module in targets:
        cmd = [sys.executable, "-m", module]
        if args.background:
            log_dir = args.log_dir
            if not os.path.isdir(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{name}_agent.log")
            with open(log_file, "a") as f:
                proc = subprocess.Popen(cmd, env=env, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
            print(f"Agente {name} en segundo plano (PID {proc.pid}), log: {log_file}")
        else:
            print(f"Arrancando {name}...")
            subprocess.run(cmd, env=env, cwd=ROOT)


if __name__ == "__main__":
    main()
