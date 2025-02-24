import abc
import math
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

import vllm
import vllm.sequence

from rrc.db.models import Provenance
from rrc.inference.prompt import get_prompt, parse_output
from rrc.utils.logger import LOGGER
from rrc.utils.ml import DEFAULT_DEVICE
from rrc.utils.types import InferenceInput, InferenceResult, InputType


def require_input_type(
    input_type: InputType,
):
    def decorator(
        func: Callable[
            ["InferenceService", list[InferenceInput]], list[InferenceResult]
        ],
    ) -> Callable[["InferenceService", list[InferenceInput]], list[InferenceResult]]:
        def wrapper(self, inputs: list[InferenceInput]) -> list[InferenceResult]:
            if any(input.input_type != input_type for input in inputs):
                raise ValueError(f"Input type for this service must be {input_type}")
            return func(self, inputs)

        return wrapper

    return decorator


class InferenceService(abc.ABC):
    """Abstract base class for inference services."""

    options: dict[str, Any]

    def __init__(self, options: dict[str, Any] | None = None):
        if options is None:
            options = {}
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abc.abstractmethod
    def predict(self, inputs: list[InferenceInput]) -> list[InferenceResult | None]:
        pass

    @abc.abstractmethod
    def get_provenance(self) -> Provenance:
        pass


_MISTRAL_ANSWER_TOKEN_MAP = {True: 5613, False: 2501}


class MistralInferenceService(InferenceService):
    model_name_or_path: str
    model_download_dir: Path
    vllm_model: vllm.LLM

    def __init__(self, options: dict[str, Any] = None):
        super().__init__(options)
        self.model_name_or_path = self.options.get("model_name_or_path")
        self.model_download_dir = self.options.get("model_download_dir")

    def __enter__(self):
        self.vllm_model = vllm.LLM(
            model=self.model_name_or_path,
            device=DEFAULT_DEVICE,
            enforce_eager=True,
            download_dir=self.model_download_dir,
            max_model_len=8192,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # TODO: Should we to purge the VLLM model?
        pass

    @require_input_type(InputType.TEXT)
    def predict(self, inputs: list[InferenceInput]) -> list[InferenceResult | None]:
        prompts = [get_prompt(input) for input in inputs]
        results: list[vllm.RequestOutput] = self.vllm_model.generate(
            prompts,
            sampling_params=vllm.SamplingParams(
                max_tokens=256,
                temperature=0.0,
                logprobs=10,
            ),
        )
        parsed_results = [self._parse_output(result) for result in results]
        for result, input in zip(parsed_results, inputs, strict=True):
            if result is None:
                continue
            result.input = input
        return parsed_results

    def _parse_output(self, output: vllm.RequestOutput) -> InferenceResult | None:
        try:
            chosen_output = output.outputs[0]
            parsed_output = parse_output(chosen_output.text)
            parsed_output.confidence = self._compute_confidence(
                chosen_output.logprobs[0], parsed_output.answer
            )
            return parsed_output
        except Exception:
            LOGGER.error(
                "Error parsing output (output: '%s'): %s",
                chosen_output.text,
                traceback.format_exc(),
            )
            return None

    def _compute_confidence(
        self, first_token_logprobs: dict[int, vllm.sequence.Logprob], answer: bool
    ) -> float:
        yes_no_logprobs = [
            first_token_logprobs[_MISTRAL_ANSWER_TOKEN_MAP[True]].logprob
            if _MISTRAL_ANSWER_TOKEN_MAP[True] in first_token_logprobs
            else 0.0,
            first_token_logprobs[_MISTRAL_ANSWER_TOKEN_MAP[False]].logprob
            if _MISTRAL_ANSWER_TOKEN_MAP[False] in first_token_logprobs
            else 0.0,
        ]
        return math.exp(yes_no_logprobs[0]) / sum(math.exp(x) for x in yes_no_logprobs)

    def get_provenance(self) -> Provenance:
        return Provenance(
            model_name=self.model_name_or_path,
            record_type="covenant_predictions",
            creator=None,
        )
