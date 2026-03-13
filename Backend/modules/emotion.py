"""
Emotion Detection Module
Analyzes emotion from image and returns one of:
focused | stressed | neutral
"""

import base64
import logging
from io import BytesIO

import numpy as np
from PIL import Image

EMOTION_STRESSED = "stressed"
EMOTION_FOCUSED = "focused"
EMOTION_NEUTRAL = "neutral"
ALLOWED_EMOTIONS = {EMOTION_STRESSED, EMOTION_FOCUSED, EMOTION_NEUTRAL}

logger = logging.getLogger(__name__)


def normalize_emotion_label(value):
    """Normalize any incoming label to strict, lowercase app labels."""
    text = str(value or "").strip().lower()
    if text in ALLOWED_EMOTIONS:
        return text
    return EMOTION_NEUTRAL


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
        image_data = base64.b64decode(base64_image)

        if len(image_data) < 100:
            return {
                "emotion": EMOTION_NEUTRAL,
                "confidence": 0.5,
                "message": "Image quality too low, using neutral detection",
            }

        try:
            from deepface import DeepFace
        except Exception as import_err:
            logger.exception("DeepFace import error: %s", str(import_err))
            return {
                "emotion": EMOTION_NEUTRAL,
                "confidence": 0.6,
                "message": "DeepFace not installed; using neutral detection",
            }

        image = Image.open(BytesIO(image_data)).convert("RGB")
        img_array = np.array(image)

        analysis = DeepFace.analyze(
            img_array,
            actions=["emotion"],
            enforce_detection=False,
        )

        if isinstance(analysis, list):
            analysis = analysis[0]

        dominant = str(analysis.get("dominant_emotion", EMOTION_NEUTRAL)).strip().lower()
        scores = analysis.get("emotion", {})

        raw_conf = scores.get(dominant, 0.0)
        confidence = max(0.0, min(1.0, round(raw_conf / 100.0, 2)))

        emotion = map_deepface_emotion(dominant)

        return {
            "emotion": emotion,
            "confidence": confidence,
            "message": emotion_message(emotion),
        }

    except Exception as exc:
        logger.exception("Emotion detection error: %s", str(exc))
        return {
            "emotion": EMOTION_NEUTRAL,
            "confidence": 0.6,
            "message": "Error processing image, using neutral detection",
        }


def get_mock_emotion():
    """Deterministic fallback for demos/offline mode."""
    return {
        "emotion": EMOTION_NEUTRAL,
        "confidence": 0.6,
        "message": emotion_message(EMOTION_NEUTRAL),
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
