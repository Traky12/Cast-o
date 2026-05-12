# backend/ai/sandbox_manager.py — Sandboxing automático para nodos sospechosos

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_K8S: Any = None
try:
    from kubernetes import client as k8s_client
    _K8S = k8s_client
except ImportError:
    pass


class SandboxManager:
    """
    Gestiona sandboxes para aislar nodos sospechosos.
    Sin cliente Kubernetes disponible, create_sandbox devuelve resultado simulado.
    """

    def __init__(self, kubernetes_client: Any = None) -> None:
        self.k8s = kubernetes_client
        self.sandbox_namespace = "sandbox-environment"

    def _ensure_sandbox_namespace(self) -> None:
        if not self.k8s or not callable(getattr(self.k8s, "create_namespace", None)):
            return
        try:
            from kubernetes.client import V1Namespace, V1ObjectMeta
            ns = V1Namespace(metadata=V1ObjectMeta(name=self.sandbox_namespace))
            self.k8s.create_namespace(ns)
        except Exception as e:
            if "AlreadyExists" not in str(e):
                logger.warning("No se pudo crear namespace sandbox: %s", e)

    def create_sandbox(self, node_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un sandbox para un nodo sospechoso (deployment aislado)."""
        sandbox_name = f"sandbox-{node_id}-{int(time.time())}".replace(".", "-")[:63]
        evidence_hash = evidence.get("evidence_hash", "unknown")

        if not self.k8s:
            logger.info("Sandbox simulado (sin cliente K8s): %s para nodo %s", sandbox_name, node_id)
            return {
                "status": "created",
                "sandbox_name": sandbox_name,
                "namespace": self.sandbox_namespace,
                "original_node": node_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "simulated": True,
            }

        self._ensure_sandbox_namespace()
        try:
            from kubernetes.client import (
                V1Capabilities,
                V1Container,
                V1Deployment,
                V1DeploymentSpec,
                V1EnvVar,
                V1PodSpec,
                V1PodTemplateSpec,
                V1ResourceRequirements,
                V1SecurityContext,
                AppsV1Api,
            )
            from kubernetes.client.models import V1ObjectMeta

            api = None
            if hasattr(self.k8s, "create_namespaced_deployment"):
                api = self.k8s
            elif _K8S:
                try:
                    api = _K8S.AppsV1Api(self.k8s) if getattr(self.k8s, "configuration", None) else _K8S.AppsV1Api()
                except Exception:
                    api = None
            if api is None and hasattr(self.k8s, "apps_v1_api"):
                api = self.k8s.apps_v1_api

            if api is None:
                return {
                    "status": "created",
                    "sandbox_name": sandbox_name,
                    "namespace": self.sandbox_namespace,
                    "original_node": node_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "simulated": True,
                }

            deployment = V1Deployment(
                metadata=V1ObjectMeta(
                    name=sandbox_name,
                    namespace=self.sandbox_namespace,
                    labels={"app": "sandboxed-node", "original-node": node_id[:63]},
                ),
                spec=V1DeploymentSpec(
                    replicas=1,
                    selector={"matchLabels": {"app": "sandboxed-node"}},
                    template=V1PodTemplateSpec(
                        metadata=V1ObjectMeta(labels={"app": "sandboxed-node"}),
                        spec=V1PodSpec(
                            security_context=V1SecurityContext(
                                run_as_non_root=True,
                                run_as_user=1000,
                                fs_group=2000,
                                read_only_root_filesystem=True,
                            ),
                            containers=[
                                V1Container(
                                    name="sandboxed-container",
                                    image="ghcr.io/tu-organizacion/sandbox-environment:v1.0",
                                    security_context=V1SecurityContext(
                                        allow_privilege_escalation=False,
                                        capabilities=V1Capabilities(drop=["ALL"]),
                                    ),
                                    resources=V1ResourceRequirements(
                                        limits={"cpu": "500m", "memory": "512Mi"},
                                    ),
                                    env=[
                                        V1EnvVar(name="ORIGINAL_NODE_ID", value=node_id),
                                        V1EnvVar(name="EVIDENCE_HASH", value=evidence_hash),
                                        V1EnvVar(name="SANDBOX_MODE", value="analysis"),
                                    ],
                                )
                            ],
                        ),
                    ),
                ),
            )
            api.create_namespaced_deployment(namespace=self.sandbox_namespace, body=deployment)
            return {
                "status": "created",
                "sandbox_name": sandbox_name,
                "namespace": self.sandbox_namespace,
                "original_node": node_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.exception("Error creando sandbox para %s: %s", node_id, e)
            return {
                "status": "failed",
                "error": str(e),
                "node_id": node_id,
                "sandbox_name": sandbox_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
