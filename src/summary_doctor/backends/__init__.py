from summary_doctor.backends.base import Backend
from summary_doctor.backends.mock import MockBackend


def get_backend(*, mock: bool, backend: str = "anthropic", model: str) -> Backend:
    if mock:
        return MockBackend()
    if backend == "claude-cli":
        from summary_doctor.backends.claude_cli import ClaudeCliBackend
        return ClaudeCliBackend(model_id=model)
    if backend == "anthropic":
        from summary_doctor.backends.anthropic import AnthropicBackend
        return AnthropicBackend(model_id=model)
    raise RuntimeError(f"unknown backend: {backend}")
