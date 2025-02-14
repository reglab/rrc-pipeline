from enum import Enum

from pydantic import BaseModel, computed_field, model_validator


class InputType(Enum):
    TEXT = "text"
    IMAGE = "image"


class InferenceInput(BaseModel):
    text: str | None = None
    image: bytes | None = None

    @model_validator(mode="after")
    def validate_input(self):
        if self.text is None and self.image is None:
            raise ValueError("Either text or image must be provided")
        return self

    @computed_field
    @property
    def input_type(self) -> InputType:
        if self.text is not None:
            return InputType.TEXT
        return InputType.IMAGE


class InferenceResult(BaseModel):
    answer: bool
    raw_passage: str | None
    quotation: str | None
    confidence: float | None

    input: InferenceInput | None = None


class OCRInput(BaseModel):
    image: bytes


class OCRResult(BaseModel):
    text: str
    input: OCRInput
