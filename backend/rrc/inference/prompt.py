import re

from rrc.utils.types import InferenceInput, InferenceResult

PROMPT_TEMPLATE = """### Instruction:
Determine whether the property deed contains a racial covenant. A racial covenant is a clause in a document that \
restricts who can reside, own, or occupy a property on the basis of race, ethnicity, national origin, or religion. \
Answer "Yes" or "No". If "Yes", provide the exact text of the relevant passage and then a quotation of the passage \
with spelling and formatting errors fixed.

### Input:
{document}

### Response:
[ANSWER]"""


def get_prompt(input: InferenceInput) -> str:
    if input.text is None:
        raise ValueError("Text input is required for text inference")
    return PROMPT_TEMPLATE.format(document=input.text)


ANSWER_REGEX = re.compile(r"(Yes|No)\[/ANSWER\]")
RAW_PASSAGE_REGEX = re.compile(r"\[RAW PASSAGE\](.*?)\[/RAW PASSAGE\]", re.DOTALL)
QUOTATION_REGEX = re.compile(r"\[QUOTATION\](.*?)\[/QUOTATION\]", re.DOTALL)


def parse_output(output: str) -> InferenceResult:
    answer_match = ANSWER_REGEX.search(output)
    if answer_match is None:
        raise ValueError("No answer found in output")
    answer = answer_match.group(1) == "Yes"
    raw_passage_match = RAW_PASSAGE_REGEX.search(output)
    quotation_match = QUOTATION_REGEX.search(output)
    return InferenceResult(
        answer=answer,
        raw_passage=(
            raw_passage_match.group(1) if answer and raw_passage_match else None
        ),
        quotation=(quotation_match.group(1) if answer and quotation_match else None),
        confidence=None,
    )
