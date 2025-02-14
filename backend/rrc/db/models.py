from __future__ import annotations

import datetime
from pathlib import Path

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from rrc.utils.types import InferenceInput, OCRInput


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class Page(Base, TimestampMixin):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_path: Mapped[str] = mapped_column(index=True)
    image_frame_idx: Mapped[int | None] = mapped_column()

    transcriptions: Mapped[list[Transcription]] = relationship(back_populates="page")
    predictions: Mapped[list[CovenantPrediction]] = relationship(back_populates="page")

    def as_text_input(self) -> InferenceInput:
        return InferenceInput(text=self.transcriptions[0].text)

    def as_image_input(self) -> InferenceInput:
        return InferenceInput(image=Path(self.image_path).read_bytes())

    def as_ocr_input(self) -> OCRInput:
        return OCRInput(image=Path(self.image_path).read_bytes())


class Transcription(Base, TimestampMixin):
    __tablename__ = "transcriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column()

    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), index=True)
    provenance_id: Mapped[int] = mapped_column(ForeignKey("provenances.id"), index=True)

    page: Mapped[Page] = relationship(back_populates="transcriptions")
    predictions: Mapped[list[CovenantPrediction]] = relationship(
        back_populates="transcription"
    )
    provenance: Mapped[Provenance] = relationship(back_populates="transcriptions")


class CovenantPrediction(Base, TimestampMixin):
    """A prediction of whether the page contains a racial covenant."""

    __tablename__ = "covenant_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    answer: Mapped[bool] = mapped_column()
    confidence: Mapped[float | None] = mapped_column()
    raw_passage: Mapped[str | None] = mapped_column()
    """If answer is true, the raw text of the passage that contains the covenant."""
    quotation: Mapped[str | None] = mapped_column()
    """If answer is true, the cleaned quotation from the passage that contains the covenant."""

    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), index=True)
    transcription_id: Mapped[int | None] = mapped_column(
        ForeignKey("transcriptions.id"), index=True
    )
    provenance_id: Mapped[int] = mapped_column(ForeignKey("provenances.id"), index=True)

    page: Mapped[Page] = relationship(back_populates="predictions")
    transcription: Mapped[Transcription] = relationship(back_populates="predictions")
    provenance: Mapped[Provenance] = relationship(back_populates="predictions")


class Provenance(Base, TimestampMixin):
    """
    A provenance record for a prediction or transcription.

    Used to track which model made the prediction or transcription.
    """

    __tablename__ = "provenances"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(index=True)
    """Name of the model which made the prediction or transcription."""
    record_type: Mapped[str] = mapped_column(index=True)
    """Either "covenant_predictions" or "transcriptions"."""
    creator: Mapped[str] = mapped_column(index=True)
    """Name of the script which created the record."""

    predictions: Mapped[list[CovenantPrediction]] = relationship(
        back_populates="provenance"
    )
    transcriptions: Mapped[list[Transcription]] = relationship(
        back_populates="provenance"
    )
