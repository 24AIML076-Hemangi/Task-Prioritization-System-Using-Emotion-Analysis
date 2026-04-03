"""
Emotion Detection Module
Analyzes emotion from image and returns one of:
focused | stressed | neutral
"""

import base64
import logging
import os
from io import BytesIO

import numpy as np
from PIL import Image

EMOTION_STRESSED = "stressed"
EMOTION_FOCUSED = "focused"
EMOTION_NEUTRAL = "neutral"
ALLOWED_EMOTIONS = {EMOTION_STRESSED, EMOTION_FOCUSED, EMOTION_NEUTRAL}

logger = logging.getLogger(__name__)
_DEEPFACE_READY = False
_DEEPFACE_ERROR = None


def preload_deepface_model():
    """Warm up DeepFace emotion model and ensure weights directory exists."""
    global _DEEPFACE_READY, _DEEPFACE_ERROR
    if _DEEPFACE_READY:
        return True
    try:
        from deepface import DeepFace
        weights_dir = os.path.expanduser("~/.deepface/weights")
        os.makedirs(weights_dir, exist_ok=True)
        DeepFace.build_model("Emotion")
        _DEEPFACE_READY = True
        return True
    except Exception as exc:
        _DEEPFACE_ERROR = str(exc)
        logger.exception("DeepFace preload error: %s", _DEEPFACE_ERROR)
        return False


def normalize_emotion_label(value):
    """Normalize any incoming label to strict, lowercase app labels."""
    text = str(value or "").strip().lower()
    if text in ALLOWED_EMOTIONS:
        return text
    return EMOTION_NEUTRAL


def _clean_base64_image(base64_image):
    """Strip data URL prefix and fix padding so base64 decoding is reliable."""
    raw = str(base64_image or "").strip()
    if not raw:
        return ""
    if "," in raw and raw.lower().startswith("data:image"):
        raw = raw.split(",", 1)[1]
    # Fix missing padding if needed
    padding = (-len(raw)) % 4
    if padding:
        raw = f"{raw}{'=' * padding}"
    return raw


def detect_emotion_from_image(base64_image):
    """
    Detect emotion from base64 encoded image

    Args:
        base64_image (str): Base64 encoded image string (JPEG)

    Returns:
        dict: {
            'emotion': 'focused' | 'stressed' | 'neutral',
            'confidence': float (0-1),
            'message': str (human-readable description)
        }
    """
    try:
        cleaned = _clean_base64_image(base64_image)
        image_data = base64.b64decode(cleaned)

        if len(image_data) < 100:
            return {
                "emotion": EMOTION_NEUTRAL,
                "confidence": 0.5,
                "message": "Image quality too low, using neutral detection",
                "debug": {
                    "source": "low_quality",
                    "dominant_emotion": EMOTION_NEUTRAL,
                    "scores": {},
                },
            }

        try:
            from deepface import DeepFace
        except Exception as import_err:
            logger.exception("DeepFace import error: %s", str(import_err))
            return {
                "emotion": EMOTION_NEUTRAL,
                "confidence": 0.6,
                "message": "DeepFace not installed; using neutral detection",
                "debug": {
                    "source": "missing_deepface",
                    "dominant_emotion": EMOTION_NEUTRAL,
                    "scores": {},
                },
            }
        if not preload_deepface_model():
            return {
                "emotion": EMOTION_NEUTRAL,
                "confidence": 0.6,
                "message": "DeepFace model not ready; using neutral detection",
                "debug": {
                    "source": "model_not_ready",
                    "dominant_emotion": EMOTION_NEUTRAL,
                    "scores": {},
                    "error": _DEEPFACE_ERROR,
                },
            }

        image = Image.open(BytesIO(image_data)).convert("RGB")
        img_array = np.array(image)

        # Try to extract the best face first; this avoids "neutral" outputs when the
        # full frame contains a small or partially visible face.
        faces = []
        try:
            faces = DeepFace.extract_faces(
                img_array,
                detector_backend="retinaface",
                enforce_detection=False,
                align=True,
            )
        except Exception:
            faces = []

        best_face = None
        best_face_area = 0
        if isinstance(faces, list):
            for face in faces:
                area = 0
                facial_area = face.get("facial_area") or {}
                w = facial_area.get("w") or facial_area.get("width") or 0
                h = facial_area.get("h") or facial_area.get("height") or 0
                area = float(w) * float(h)
                if area > best_face_area:
                    best_face_area = area
                    best_face = face

        if not best_face or best_face_area <= 0:
            return {
                "emotion": EMOTION_NEUTRAL,
                "confidence": 0.4,
                "message": "No face detected. Move closer and keep your face centered.",
                "debug": {
                    "source": "no_face",
                    "dominant_emotion": EMOTION_NEUTRAL,
                    "scores": {},
                },
            }

        face_img = best_face.get("face") if isinstance(best_face, dict) else None
        if face_img is None:
            face_img = img_array

        analysis = DeepFace.analyze(
            face_img,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend="retinaface",
            align=True,
        )

        if isinstance(analysis, list):
            analysis = analysis[0]

        dominant = str(analysis.get("dominant_emotion", EMOTION_NEUTRAL)).strip().lower()
        scores = analysis.get("emotion", {}) or {}

        if scores:
            best_raw_emotion = max(scores, key=scores.get)
            raw_conf = scores.get(best_raw_emotion, 0.0)
        else:
            best_raw_emotion = dominant
            raw_conf = 0.0

        confidence = max(0.0, min(1.0, round(float(raw_conf) / 100.0, 2)))

        # If a target emotion is close to the top score, prefer it to avoid neutral bias.
        if scores:
            top_score = float(scores.get(best_raw_emotion, 0.0))
            sad_score = float(scores.get("sad", 0.0))
            if best_raw_emotion != "sad" and sad_score >= 20 and (top_score - sad_score) <= 5:
                best_raw_emotion = "sad"
            else:
                happy_score = float(scores.get("happy", 0.0))
                if best_raw_emotion not in {"happy", "surprise"} and happy_score >= 20 and (top_score - happy_score) <= 5:
                    best_raw_emotion = "happy"

        emotion = map_deepface_emotion(best_raw_emotion or dominant)

        return {
            "emotion": emotion,
            "confidence": confidence,
            "message": emotion_message(emotion),
            "debug": {
                "source": "deepface",
                "dominant_emotion": dominant,
                "best_emotion": best_raw_emotion,
                "scores": scores,
                "face_area": best_face_area,
            },
        }

    except Exception as exc:
        logger.exception("Emotion detection error: %s", str(exc))
        return {
            "emotion": EMOTION_NEUTRAL,
            "confidence": 0.6,
            "message": "Error processing image, using neutral detection",
            "debug": {
                "source": "error",
                "dominant_emotion": EMOTION_NEUTRAL,
                "scores": {},
            },
        }


def get_mock_emotion():
    """Deterministic fallback for demos/offline mode."""
    return {
        "emotion": EMOTION_NEUTRAL,
        "confidence": 0.6,
        "message": emotion_message(EMOTION_NEUTRAL),
        "debug": {
            "source": "mock",
            "dominant_emotion": EMOTION_NEUTRAL,
            "scores": {},
        },
    }


def map_deepface_emotion(dominant_emotion):
    """
    Map DeepFace emotions to app-specific labels.
    DeepFace emotions: angry, disgust, fear, happy, sad, surprise, neutral
    """
    dominant = str(dominant_emotion or "").strip().lower()
    stressed = {"angry", "disgust", "fear", "sad"}
    focused = {"happy", "surprise"}

    if dominant in stressed:
        return EMOTION_STRESSED
    if dominant in focused:
        return EMOTION_FOCUSED
    return EMOTION_NEUTRAL


def emotion_message(emotion):
    normalized = normalize_emotion_label(emotion)
    messages = {
        EMOTION_FOCUSED: "Focus mode: prioritize deep-work, long-term, high-complexity tasks.",
        EMOTION_STRESSED: "Stress mode: start with short urgent tasks and split large tasks into subtasks.",
        EMOTION_NEUTRAL: "Neutral mode: prioritize routine planning and medium-priority tasks.",
    }
    return messages.get(normalized, messages[EMOTION_NEUTRAL])


def get_emotion_icon(emotion):
    """Map emotion to emoji icon."""
    normalized = normalize_emotion_label(emotion)
    icons = {
        EMOTION_FOCUSED: "F",
        EMOTION_STRESSED: "S",
        EMOTION_NEUTRAL: "N",
    }
    return icons.get(normalized, "N")
