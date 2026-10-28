from typing import Any

from pydantic import TypeAdapter

from build.schemas.route import CheckedSpeed, Speed
from tests.builders.evidence import make_evidence

_SPEED = TypeAdapter(CheckedSpeed)


def make_speed(tokens_per_second: float = 70.0, time_to_first_token_s: float = 3.8, **overrides: Any) -> Speed:
    """A route's measured generation speed. By default 70 tokens per second and 3.8 s to the first token, from
    OpenRouter's providers page."""
    return _SPEED.validate_python(
        {
            "tokens_per_second": tokens_per_second,
            "time_to_first_token_s": time_to_first_token_s,
            "evidence": [
                make_evidence(
                    kind="corroborating",
                    url="https://openrouter.ai/acme/m-70b/providers",
                    shows='Performance, 1 week: "Acme Avg 70 tok/s", "Acme Avg 3.8 s"',
                )
            ],
        }
        | overrides
    )
