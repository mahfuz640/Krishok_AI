"""Krishok AI rice leaf inference API."""
from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.getenv("KRISHOK_MODEL_PATH", ROOT / "AI/experiments/MobileNetV3_Rice/best_model.pt"))
MODEL_SHA256 = "99bd70c5fa8ee99c1d578c44e6099cd8133499ddfdaf1609180cf6530846e5b0"
CLASSES = ["Blast", "Brown spot", "Healthy", "Leaf smut", "Rice Tungro", "Sheath blight"]
MAX_IMAGE_BYTES = 10 * 1024 * 1024

app = FastAPI(title="Krishok AI API", version="1.0.0")
origins = [item.strip() for item in os.getenv("KRISHOK_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])
model: Any = None
torch: Any = None
transforms: Any = None
model_error: str | None = None


@app.on_event("startup")
def load_model() -> None:
    global model, torch, transforms, model_error
    if not MODEL_PATH.is_file():
        model_error = f"Model file not found: {MODEL_PATH}"
        return
    try:
        import hashlib
        import torch as torch_module
        from torchvision import models, transforms as transform_module

        digest = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
        if digest != MODEL_SHA256:
            raise RuntimeError("Model SHA-256 does not match the approved checkpoint.")
        torch = torch_module
        transforms = transform_module
        network = models.mobilenet_v3_large(weights=None)
        network.classifier[-1] = torch.nn.Linear(network.classifier[-1].in_features, len(CLASSES))
        checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
        state = checkpoint.get("model_state_dict", checkpoint.get("state_dict", checkpoint)) if isinstance(checkpoint, dict) else checkpoint
        network.load_state_dict(state)
        model = network.eval()
    except Exception as exc:  # Keep health endpoint available when optional ML dependencies are absent.
        model_error = str(exc)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "modelReady": model is not None, "modelVersion": "mobilenetv3-large-rice-v1", "classes": CLASSES, "message": None if model else model_error}


@app.post("/v1/rice/detect")
async def detect(image: UploadFile = File(...)) -> dict[str, Any]:
    if model is None:
        raise HTTPException(status_code=503, detail="Rice disease detection is unavailable: model runtime is not ready.")
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WebP leaf image.")
    content = await image.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        with Image.open(BytesIO(content)) as source:
            rgb = ImageOps.exif_transpose(source).convert("RGB")
            pipeline = transforms.Compose([
                transforms.Resize(232, interpolation=transforms.InterpolationMode.BILINEAR, antialias=True),
                transforms.CenterCrop(224), transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
            tensor = pipeline(rgb).unsqueeze(0)
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable image.") from None
    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor)[0], dim=0)
        confidence, class_id = probabilities.max(dim=0)
    return {"classId": int(class_id.item()), "confidence": float(confidence.item()), "diseaseName": CLASSES[int(class_id.item())], "modelVersion": "mobilenetv3-large-rice-v1", "mode": "online"}
