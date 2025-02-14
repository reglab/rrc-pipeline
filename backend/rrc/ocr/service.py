import abc
from io import BytesIO
from typing import Any

import doctr.io
import numpy as np
from doctr.models import ocr_predictor
from PIL import Image

from rrc.db.models import Provenance
from rrc.utils.logger import LOGGER
from rrc.utils.ml import DEFAULT_DEVICE
from rrc.utils.types import OCRInput, OCRResult


class OCRService(abc.ABC):
    """Abstract base class for OCR services."""

    options: dict[str, Any]

    def __init__(self, options: dict[str, Any] | None = None):
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abc.abstractmethod
    def predict(self, inputs: list[OCRInput]) -> list[OCRResult]:
        pass

    @abc.abstractmethod
    def get_provenance(self) -> Provenance:
        pass


_DOCTR_DET_ARCH = "db_resnet50"
_DOCTR_RECO_ARCH = "crnn_vgg16_bn"


class DoctrOCRService(OCRService):
    def __init__(self, options: dict[str, Any] | None = None):
        super().__init__(options)

    def __enter__(self):
        self.model = ocr_predictor(
            det_arch=_DOCTR_DET_ARCH,
            reco_arch=_DOCTR_RECO_ARCH,
            pretrained=True,
            assume_straight_pages=True,
            det_bs=16,
            reco_bs=1024,
        ).to(DEFAULT_DEVICE)
        LOGGER.info("Doctr OCR model loaded on device %s", DEFAULT_DEVICE)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def predict(self, inputs: list[OCRInput]) -> list[OCRResult]:
        model_inputs = [self._prepare_input(input) for input in inputs]
        results: list[doctr.io.Page] = self.model(model_inputs).pages
        return [
            self._parse_output(result, input)
            for result, input in zip(results, inputs, strict=True)
        ]

    def _prepare_input(self, input: OCRInput) -> Image.Image:
        img = Image.open(BytesIO(input.image))
        return np.array(img.convert("RGB"))

    def _parse_output(self, page: doctr.io.Page, input: OCRInput) -> OCRResult:
        all_lines: list[doctr.io.Line] = []
        for block in page.blocks:
            all_lines.extend(block.lines)
        all_lines.sort(key=lambda ln: ln.geometry[0][1])
        span_boxes = {}
        output_text = ""
        for line_idx, line in enumerate(all_lines):
            for word_idx, word in enumerate(line.words):
                span = (len(output_text), len(output_text) + len(word.value))
                span_boxes[span] = (
                    word.geometry.tolist()
                    if isinstance(word.geometry, np.ndarray)
                    else word.geometry
                )
                output_text += word.value
                if word_idx < len(line.words) - 1:
                    output_text += " "
            if line_idx < len(all_lines) - 1:
                output_text += "\n"
        return OCRResult(
            text=output_text,
            input=input,
        )

    def get_provenance(self) -> Provenance:
        return Provenance(
            model_name=f"doctr.{_DOCTR_DET_ARCH}.{_DOCTR_RECO_ARCH}",
            record_type="transcriptions",
            creator=None,
        )
