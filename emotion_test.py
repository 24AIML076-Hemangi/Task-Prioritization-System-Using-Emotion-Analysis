import cv2
from deepface import DeepFace

EMOTION_MAP = {
    "happy": "HAPPY",
    "surprise": "HAPPY",
    "angry": "ANGER",
    "disgust": "ANGER",
    "fear": "FEAR",
    "sad": "SAD",
    "neutral": "SAD"
}

def get_age_group(age):
    if age <= 12:
        return "CHILD"
    elif age <= 19:
        return "TEEN"
    elif age <= 30:
        return "YOUNG_ADULT"
    elif age <= 50:
        return "ADULT"
    else:
        return "SENIOR"

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = cv2.VideoCapture(0)

frame_count = 0
emotion = "SAD"
age_group = "UNKNOWN"

print("🔥 Emotion + Age Detection Started (NO GENDER)")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(60, 60)
    )

    for (x, y, w, h) in faces:
        face_roi = frame[y:y+h, x:x+w]
        if face_roi.size == 0:
            continue

        # Heavy ML only every 20 frames
        if frame_count % 20 == 0:
            try:
                result = DeepFace.analyze(
                    face_roi,
                    actions=["emotion", "age"],
                    enforce_detection=True
                )

                data = result[0] if isinstance(result, list) else result

                raw_emotion = data["dominant_emotion"]
                emotion = EMOTION_MAP.get(raw_emotion, "SAD")

                age = int(data["age"])
                age_group = get_age_group(age)

            except Exception as e:
                print("Analysis error:", e)

        label = f"{emotion} | {age_group}"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(
            frame,
            label,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow("Emotion + Age", frame)
    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
