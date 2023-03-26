from pydantic.dataclasses import dataclass
import typing as T


@dataclass
class FaceResult:
    face_name: T.Optional[str] = None
    match_result: T.Optional[float] = None
    emotion: T.Optional[str] = None

@dataclass
class FaceCrop:
    original_face: bytes
    face_with_alpha_background: bytes
