from summary_doctor.backends.base import Backend
from summary_doctor.backends.mock import MockBackend


def get_backend(*, mock: bool, model: str) -> Backend:
    if mock:
        return MockBackend()
    from summary_doctor.backends.anthropic import AnthropicBackend
    return AnthropicBackend(model_id=model)
