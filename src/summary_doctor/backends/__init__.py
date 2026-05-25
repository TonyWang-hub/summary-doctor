from summary_doctor.backends.base import Backend
from summary_doctor.backends.mock import MockBackend


def get_backend(
    *,
    mock: bool,
    backend: str = "anthropic",
    model: str,
    cache_ttl: str | None = "5m",
) -> Backend:
    if mock:
        return MockBackend()
    if backend == "claude-cli":
        from summary_doctor.backends.claude_cli import ClaudeCliBackend
        # claude-cli backend cannot control cache_control externally —
        # cache is managed by the subscription. cache_ttl is ignored here.
        return ClaudeCliBackend(model_id=model)
    if backend == "anthropic":
        from summary_doctor.backends.anthropic import AnthropicBackend
        return AnthropicBackend(model_id=model, cache_ttl=cache_ttl)
    raise RuntimeError(f"unknown backend: {backend}")
