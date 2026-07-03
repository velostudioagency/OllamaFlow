"""
Token Cost Tracker

Tracks token usage and estimated costs across workflow runs.
Supports Ollama (free/local), Groq, OpenAI, and Anthropic pricing.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import time


# Pricing per 1M tokens (USD)
MODEL_PRICING = {
    # Groq models (free tier, but tracking tokens)
    "groq:llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},
    "groq:llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
    "groq:gemma2-9b-it": {"input": 0.0, "output": 0.0},
    "groq:mixtral-8x7b-32768": {"input": 0.0, "output": 0.0},
    "groq:meta-llama/llama-4-scout-17b-16e-instruct": {"input": 0.0, "output": 0.0},

    # OpenAI models
    "openai:gpt-4o": {"input": 2.50, "output": 10.00},
    "openai:gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai:gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "openai:gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "openai:o1": {"input": 15.00, "output": 60.00},
    "openai:o1-mini": {"input": 3.00, "output": 12.00},

    # Anthropic models
    "anthropic:claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "anthropic:claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "anthropic:claude-3-opus-20240229": {"input": 15.00, "output": 75.00},

    # Ollama models (free/local)
    "ollama:default": {"input": 0.0, "output": 0.0},
}

# Fallback: unknown models treated as free
DEFAULT_PRICING = {"input": 0.0, "output": 0.0}


@dataclass
class NodeTokenUsage:
    """Token usage for a single node."""
    node_id: str
    node_type: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0


@dataclass
class WorkflowTokenUsage:
    """Aggregated token usage for an entire workflow run."""
    nodes: List[NodeTokenUsage] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost: float = 0.0
    duration_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_type": n.node_type,
                    "provider": n.provider,
                    "model": n.model,
                    "prompt_tokens": n.prompt_tokens,
                    "completion_tokens": n.completion_tokens,
                    "total_tokens": n.total_tokens,
                    "estimated_cost": round(n.estimated_cost, 6),
                }
                for n in self.nodes
            ],
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_estimated_cost": round(self.total_estimated_cost, 6),
            "duration_ms": round(self.duration_ms, 1),
        }


class TokenCostTracker:
    """Tracks token usage and costs during workflow execution."""

    def __init__(self):
        self._node_usages: Dict[str, NodeTokenUsage] = {}
        self._start_time: float = 0

    def start(self):
        """Start tracking a new workflow run."""
        self._node_usages.clear()
        self._start_time = time.monotonic()

    def record_node_usage(
        self,
        node_id: str,
        node_type: str,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ):
        """Record token usage for a node."""
        total = prompt_tokens + completion_tokens
        pricing_key = f"{provider}:{model}"
        pricing = MODEL_PRICING.get(pricing_key, DEFAULT_PRICING)

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        estimated_cost = input_cost + output_cost

        usage = NodeTokenUsage(
            node_id=node_id,
            node_type=node_type,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            estimated_cost=estimated_cost,
        )
        self._node_usages[node_id] = usage

    def get_summary(self) -> WorkflowTokenUsage:
        """Get aggregated token usage summary."""
        duration_ms = (time.monotonic() - self._start_time) * 1000

        summary = WorkflowTokenUsage(
            nodes=list(self._node_usages.values()),
            duration_ms=duration_ms,
        )

        for usage in self._node_usages.values():
            summary.total_prompt_tokens += usage.prompt_tokens
            summary.total_completion_tokens += usage.completion_tokens
            summary.total_tokens += usage.total_tokens
            summary.total_estimated_cost += usage.estimated_cost

        return summary

    def get_node_usage(self, node_id: str) -> Optional[NodeTokenUsage]:
        """Get token usage for a specific node."""
        return self._node_usages.get(node_id)


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (4 chars per token)."""
    return max(1, len(text) // 4)
