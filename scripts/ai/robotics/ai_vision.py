#!/usr/bin/env python3
"""
Visión mínima para lab: mock sin cámara, o CNN ligera con pooling adaptativo (sin tamaño fijo ficticio en entrada).
Producción exige calibración, conjunto de datos y evaluación de seguridad (DPIA, paradas).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Tuple

import numpy as np


def detect_mock(frame: np.ndarray) -> Dict[str, Any]:
    m = float(np.mean(frame)) / 255.0 if frame.size else 0.0
    return {"label": "mock_mean", "class_id": 0, "confidence": float(min(1.0, max(0.0, m + 0.15)))}


class TinyVisionNet:
    """CNN pequeña + AdaptiveAvgPool2d(1) → vector fijo."""

    def __init__(self) -> None:
        import torch
        import torch.nn as nn

        self._torch = torch
        self.net = nn.Sequential(
            nn.Conv2d(3, 8, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(8, 3),
        )

    def infer(self, frame_bgr: np.ndarray) -> Dict[str, Any]:
        torch = self._torch
        rgb = frame_bgr[:, :, ::-1].astype(np.float32) / 255.0
        t = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0)
        self.net.eval()
        with torch.no_grad():
            logits = self.net(t)
            prob = torch.softmax(logits, dim=1)[0]
            class_id = int(torch.argmax(prob).item())
        labels = ("low_signal", "mid_signal", "high_signal")
        return {
            "label": labels[class_id],
            "class_id": class_id,
            "confidence": float(prob[class_id].item()),
        }


def detect(frame: np.ndarray, *, use_torch: bool = False) -> Dict[str, Any]:
    mock = os.environ.get("CASTUO_VISION_MOCK", "").lower() in ("1", "true", "yes")
    if mock or not use_torch:
        return detect_mock(frame)
    net = TinyVisionNet()
    return net.infer(frame)


def main() -> None:
    p = argparse.ArgumentParser(description="Detección lab (mock por defecto; --camera requiere OpenCV).")
    p.add_argument("--camera", action="store_true", help="Bucle cámara (OpenCV); sin flag: una pasada mock")
    p.add_argument("--torch", action="store_true", help="Usar CNN PyTorch (sin mock forzado)")
    args = p.parse_args()

    if args.camera:
        try:
            import cv2
        except ImportError as e:
            raise SystemExit("pip install opencv-python-headless (o requirements_robotics_vision.txt)") from e
        cap = cv2.VideoCapture(0)
        net_torch = args.torch and os.environ.get("CASTUO_VISION_MOCK", "").lower() not in ("1", "true", "yes")
        d: Dict[str, Any] = detect_mock(np.zeros((8, 8, 3), dtype=np.uint8))
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            d = detect(frame, use_torch=net_torch)
            cv2.putText(frame, d["label"], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)
            cv2.imshow("castuo-robotics-vision", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()
        print(json.dumps({"last": d}, ensure_ascii=False))
        return

    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    frame[:, :] = (40, 120, 80)
    d = detect(frame, use_torch=args.torch)
    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
