"""Resiliência: políticas puras e executor com retry/backoff (research/02 §7-§9)."""

from bai_supabase.resilience.executor import ResilienceExecutorImpl, build_executor  # noqa: F401
from bai_supabase.resilience.policies import (  # noqa: F401
    HEAVY_QUERY_CODES,
    ExecutionPolicy,
    retry_policy_from_settings,
    timeout_policy_from_settings,
)
