"""Leaf disease recognition using the plant_disease model (runs in thread)."""
import io
import os
import sys
from typing import Any

# Must set before TensorFlow import
os.environ["TF_USE_LEGACY_KERAS"] = "1"

from backend.api.settings import DISEASE_MODEL_PATH, DISEASE_CLASSES_PATH, DISEASE_MODEL_DIR

# Add model dir for any local imports
if str(DISEASE_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(DISEASE_MODEL_DIR))


def _load_model_and_classes():
    import numpy as np
    import tensorflow as tf
    from PIL import Image
    from tf_keras.applications.efficientnet import preprocess_input

    if not DISEASE_MODEL_PATH.exists():
        raise FileNotFoundError(f"Disease model not found: {DISEASE_MODEL_PATH}")
    if not DISEASE_CLASSES_PATH.exists():
        raise FileNotFoundError(f"Classes file not found: {DISEASE_CLASSES_PATH}")

    model = tf.keras.models.load_model(str(DISEASE_MODEL_PATH), compile=False)
    with open(DISEASE_CLASSES_PATH, "r") as f:
        class_names = [line.strip() for line in f.readlines() if line.strip()]
    return model, class_names, preprocess_input, np


# Lazy singleton
_model_cache: tuple | None = None


def _get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = _load_model_and_classes()
    return _model_cache


def predict_disease(image_bytes: bytes) -> dict[str, Any]:
    """
    Run disease prediction on image bytes. Returns dict with class, confidence, top.
    """
    from PIL import Image
    model, class_names, preprocess_input, np = _get_model()
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize((224, 224))
    img_array = np.array(image, dtype=np.float32)
    img_array = preprocess_input(img_array)
    img_batch = np.expand_dims(img_array, axis=0)
    predictions = model.predict(img_batch, verbose=0)
    preds = predictions[0]
    top_indices = np.argsort(preds)[-3:][::-1]
    top = [
        {"class": class_names[i], "confidence": float(preds[i])}
        for i in top_indices
    ]
    idx = int(np.argmax(preds))
    return {
        "class": class_names[idx],
        "confidence": float(np.max(preds)),
        "top": top,
    }
