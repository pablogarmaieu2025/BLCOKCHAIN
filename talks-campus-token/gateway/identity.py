"""The plug-in point for face recognition.

The door only needs ONE thing from the biometric side:
    "Who is this?"  ->  a student id, or None if nobody matches.

Any face recognition code that implements `FaceMatcher` can be dropped in
without changing the door or the blockchain code.

Privacy rule for every implementation:
    Face images and face templates stay on the local device (today: the door
    laptop; later: the student's phone). They are NEVER sent to the
    blockchain, to the registry, or to any server.
"""
from __future__ import annotations

from typing import Any, Optional, Protocol


class FaceMatcher(Protocol):
    def enroll(self, student_id: str, image: Any) -> None:
        """Stores this student's face template locally."""
        ...

    def identify(self, image: Any) -> Optional[str]:
        """Returns the matching student id, or None if no enrolled face matches."""
        ...


class DemoFaceMatcher:
    """Stand-in used until the real face recognition is plugged in.

    "Images" are just labels like "sara-photo-2" here, matched by the
    person's name before the dash. It lets us run the whole system today.
    """

    def __init__(self):
        self._enrolled: dict[str, str] = {}

    def enroll(self, student_id: str, image: Any) -> None:
        self._enrolled[str(image).split("-")[0]] = student_id

    def identify(self, image: Any) -> Optional[str]:
        return self._enrolled.get(str(image).split("-")[0])
