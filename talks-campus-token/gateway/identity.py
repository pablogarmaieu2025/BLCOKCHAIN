"""Matcher protocol and explicit mock used only for legacy unit tests."""
from typing import Any, Optional, Protocol

class FaceMatcher(Protocol):
    def enroll(self, student_id: str, image: Any) -> None: ...
    def identify(self, image: Any) -> Optional[str]: ...

class DemoFaceMatcher:
    """String-label test double; not biometric recognition."""
    def __init__(self):
        self._enrolled: dict[str, str] = {}
    def enroll(self, student_id: str, image: Any) -> None:
        self._enrolled[str(image).split("-")[0]] = student_id
    def identify(self, image: Any) -> Optional[str]:
        return self._enrolled.get(str(image).split("-")[0])
