"""
Emotion Detection Module
Analyzes emotion from image and returns emotion type with confidence score
"""

import base64
import random
from io import BytesIO

import numpy as np
from PIL import Image


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
        # Decode base64 image
        image_data = base64.b64decode(base64_image)

        if len(image_data) < 100:
            # Not a real image, return neutral with low confidence
            return {
                'emotion': 'neutral',
                'confidence': 0.5,
                'message': 'Image quality too low, using neutral detection'
            }

        try:
            from deepface import DeepFace
        except Exception as import_err:
            print(f"âŒ DeepFace import error: {str(import_err)}")
            return {
                'emotion': 'neutral',
                'confidence': 0.6,
                'message': 'DeepFace not installed; using neutral detection'
            }

        # Convert image bytes -> PIL -> numpy array
        image = Image.open(BytesIO(image_data)).convert("RGB")
        img_array = np.array(image)

        # DeepFace emotion analysis
        analysis = DeepFace.analyze(
            img_array,
            actions=["emotion"],
            enforce_detection=False
        )

        # DeepFace may return a list when multiple faces are detected
        if isinstance(analysis, list):
            analysis = analysis[0]

        dominant = analysis.get("dominant_emotion", "neutral")
        scores = analysis.get("emotion", {})

        # Confidence is reported as a percentage (0-100) in DeepFace
        raw_conf = scores.get(dominant, 0.0)
        confidence = max(0.0, min(1.0, round(raw_conf / 100.0, 2)))

        emotion = map_deepface_emotion(dominant)

        return {
            "emotion": emotion,
            "confidence": confidence,
            "message": emotion_message(emotion)
        }

    except Exception as e:
        print(f"âŒ Emotion detection error: {str(e)}")
        # Fallback to neutral emotion on error
        return {
            'emotion': 'neutral',
            'confidence': 0.6,
            'message': 'Error processing image, using neutral detection'
        }


def get_mock_emotion():
    """
    Generate realistic mock emotion detection results
    Weighted distribution to prefer focused/neutral over stressed
    """
    # Weighted random selection
    emotions = [
        {'emotion': 'focused', 'confidence': 0.85, 'weight': 4},
        {'emotion': 'neutral', 'confidence': 0.78, 'weight': 3},
        {'emotion': 'stressed', 'confidence': 0.72, 'weight': 2},
    ]

    # Create weighted list
    weighted_emotions = []
    for e in emotions:
        weighted_emotions.extend([e] * e['weight'])

    # Pick random emotion from weighted list
    selected = random.choice(weighted_emotions)

    # Add some random variation to confidence (+/-5%)
    confidence = selected['confidence'] + random.uniform(-0.05, 0.05)
    confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1

    messages = {
        'focused': 'You\'re in focus mode! Tackle high-effort tasks now.',
        'stressed': 'You seem stressed. Start with easier tasks to build momentum.',
        'neutral': 'You\'re in a balanced state. Ready for any task.',
    }

    return {
        'emotion': selected['emotion'],
        'confidence': round(confidence, 2),
        'message': messages[selected['emotion']]
    }


def map_deepface_emotion(dominant_emotion):
    """
    Map DeepFace emotions to app-specific labels.
    DeepFace emotions: angry, disgust, fear, happy, sad, surprise, neutral
    """
    stressed = {"angry", "disgust", "fear", "sad"}
    focused = {"happy", "surprise"}

    if dominant_emotion in stressed:
        return "stressed"
    if dominant_emotion in focused:
        return "focused"
    return "neutral"


def emotion_message(emotion):
    messages = {
        'focused': 'You\'re in focus mode! Tackle high-effort tasks now.',
        'stressed': 'You seem stressed. Start with easier tasks to build momentum.',
        'neutral': 'You\'re in a balanced state. Ready for any task.',
    }
    return messages.get(emotion, 'You\'re in a balanced state. Ready for any task.')


def get_emotion_icon(emotion):
    """Map emotion to emoji icon"""
    icons = {
        'focused': 'ðŸŽ¯',
        'stressed': 'ðŸ˜°',
        'neutral': 'ðŸ˜'
    }
    return icons.get(emotion, 'ðŸ˜Š')
