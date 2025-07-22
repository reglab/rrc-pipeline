import abc
import json
import math
import re
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

import vllm
import vllm.sequence
from transformers import AutoTokenizer

from rrc.db.models import Provenance
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
_MISTRAL_CONFIDENCE_THRESHOLD = 0.75


class MistralInferenceService(InferenceService):
    model_name_or_path: str
    model_download_dir: Path
    vllm_model: vllm.LLM

    _PROMPT_TEMPLATE = """### Instruction:
Determine whether the property deed contains a racial covenant. A racial covenant is a clause in a document that \
restricts who can reside, own, or occupy a property on the basis of race, ethnicity, national origin, or religion. \
Answer "Yes" or "No". If "Yes", provide the exact text of the relevant passage and then a quotation of the passage \
with spelling and formatting errors fixed.

### Input:
{document}

### Response:
[ANSWER]"""

    _ANSWER_REGEX = re.compile(r"(Yes|No)\[/ANSWER\]")
    _RAW_PASSAGE_REGEX = re.compile(r"\[RAW PASSAGE\](.*?)\[/RAW PASSAGE\]", re.DOTALL)
    _QUOTATION_REGEX = re.compile(
        r"\[CORRECTED QUOTATION\](.*?)\[/CORRECTED QUOTATION\]", re.DOTALL
    )

    def __init__(self, options: dict[str, Any] = None):
        super().__init__(options)
        self.model_name_or_path = self.options.get("model_name_or_path")
        self.model_download_dir = self.options.get("model_download_dir")

    def __enter__(self):
        if DEFAULT_DEVICE is None:
            raise RuntimeError("No CUDA or MPS device available")
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

    def _get_mistral_prompt(self, input: InferenceInput) -> str:
        if input.text is None:
            raise ValueError("Text input is required for text inference")
        return self._PROMPT_TEMPLATE.format(document=input.text)

    @require_input_type(InputType.TEXT)
    def predict(self, inputs: list[InferenceInput]) -> list[InferenceResult | None]:
        prompts = [self._get_mistral_prompt(input) for input in inputs]
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

            answer_match = self._ANSWER_REGEX.search(chosen_output.text)
            if answer_match is None:
                raise ValueError("No answer found in output")
            answer = answer_match.group(1) == "Yes"

            raw_passage_match = self._RAW_PASSAGE_REGEX.search(chosen_output.text)
            quotation_match = self._QUOTATION_REGEX.search(chosen_output.text)

            confidence = self._compute_confidence(chosen_output.logprobs[0], answer)

            return InferenceResult(
                answer=answer,
                raw_passage=(
                    raw_passage_match.group(1) if answer and raw_passage_match else None
                ),
                quotation=(
                    quotation_match.group(1) if answer and quotation_match else None
                ),
                confidence=confidence,
            )
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


_QWEN_SYSTEM_MESSAGE = """You are a legal expert which classifies whether a historical property deed contains a racially restrictive covenant, a provision which discriminates on the basis of race, ethnicity, national origin, or other protected class.

Given the text of a deed or excerpt, output a JSON object with the following fields:
- 'answer' (bool): true if the deed contains a racially restrictive covenant, false otherwise
- 'quotation' (str | None): the exact text of the covenant, if it exists
"""

_QWEN_ANSWER_TOKEN_INDEX = 5
_QWEN_ANSWER_TOKEN_MAP = {True: 830, False: 895}
_QWEN_CONFIDENCE_THRESHOLD = 0.96


class QwenInferenceService(InferenceService):
    model_name_or_path: str
    model_download_dir: Path
    vllm_model: vllm.LLM
    tokenizer: AutoTokenizer

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
            enable_prefix_caching=True,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # TODO: Should we to purge the VLLM model?
        pass

    def _get_qwen_prompt(self, input: InferenceInput) -> str:
        if input.text is None:
            raise ValueError("Text input is required for text inference")

        user_message = f"<document>{input.text}</document>"
        return self.tokenizer.apply_chat_template(
            [
                {"role": "system", "content": _QWEN_SYSTEM_MESSAGE},
                {"role": "user", "content": user_message},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )

    @require_input_type(InputType.TEXT)
    def predict(self, inputs: list[InferenceInput]) -> list[InferenceResult | None]:
        prompts = [self._get_qwen_prompt(input) for input in inputs]
        results: list[vllm.RequestOutput] = self.vllm_model.generate(
            prompts,
            sampling_params=vllm.SamplingParams(
                max_tokens=512,
                temperature=0.0,
                logprobs=8,
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
            parsed_json = json.loads(chosen_output.text)

            confidence = None
            if (
                chosen_output.logprobs is not None
                and len(chosen_output.logprobs) > _QWEN_ANSWER_TOKEN_INDEX
            ):
                confidence = self._compute_confidence(
                    chosen_output.logprobs[_QWEN_ANSWER_TOKEN_INDEX],
                    parsed_json["answer"],
                )
            actual_answer = parsed_json["answer"]
            if confidence and confidence < _QWEN_CONFIDENCE_THRESHOLD:
                actual_answer = False

            return InferenceResult(
                answer=actual_answer,
                raw_passage=parsed_json.get("quotation"),
                quotation=parsed_json.get("quotation"),
                confidence=confidence,
            )
        except Exception:
            LOGGER.error(
                "Error parsing output (output: '%s'): %s",
                chosen_output.text,
                traceback.format_exc(),
            )
            return None

    def _compute_confidence(
        self, answer_token_logprobs: dict[int, vllm.sequence.Logprob], answer: bool
    ) -> float | None:
        yes_prob = math.exp(
            answer_token_logprobs.get(
                _QWEN_ANSWER_TOKEN_MAP[True], vllm.sequence.Logprob(0.0)
            ).logprob
        )
        no_prob = math.exp(
            answer_token_logprobs.get(
                _QWEN_ANSWER_TOKEN_MAP[False], vllm.sequence.Logprob(0.0)
            ).logprob
        )
        total_prob = yes_prob + no_prob
        return yes_prob / total_prob if total_prob > 0 else None

    def get_provenance(self) -> Provenance:
        return Provenance(
            model_name=self.model_name_or_path,
            record_type="covenant_predictions",
            creator=None,
        )
