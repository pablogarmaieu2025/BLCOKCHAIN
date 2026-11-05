"""TEMPLATE for the biometric teammate: wrap your face recognition code here.

Fill in `enroll` and `identify`. Nothing else in the project needs to change:
pass an instance of this class to `Door(...)` instead of `DemoFaceMatcher`.

Important: comparing face photos with a cryptographic hash does NOT work
(two photos of the same face never give the same hash). Use face
embeddings (vectors) and a distance threshold instead, which is what
libraries like `face_recognition` (dlib) or `deepface` do.

Example below uses `face_recognition` (pip install face_recognition).
It is commented out so the project runs without it installed.
"""
from __future__ import annotations

from typing import Any, Optional

# import face_recognition  # uncomment when you plug in your code
# import numpy as np


class TeammateFaceMatcher:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold        # lower = stricter matching
        self._templates: dict[str, Any] = {}  # student_id -> face embedding, LOCAL ONLY

    def enroll(self, student_id: str, image: Any) -> None:
        # picture = face_recognition.load_image_file(image)       # image = file path
        # encodings = face_recognition.face_encodings(picture)
        # if len(encodings) != 1:
        #     raise ValueError("Enrolment photo must contain exactly one face")
        # self._templates[student_id] = encodings[0]
        raise NotImplementedError("Plug in your enrolment code here")

    def identify(self, image: Any) -> Optional[str]:
        # picture = face_recognition.load_image_file(image)
        # encodings = face_recognition.face_encodings(picture)
        # if not encodings or not self._templates:
        #     return None
        # ids = list(self._templates)
        # distances = face_recognition.face_distance([self._templates[i] for i in ids], encodings[0])
        # best = int(np.argmin(distances))
        # return ids[best] if distances[best] <= self.threshold else None
        raise NotImplementedError("Plug in your matching code here")
