"""
OllamaFlow Python SDK

Run OllamaFlow workflows from Python scripts or the command line.

Usage from Python:
    from ollamaflow import OllamaFlow

    client = OllamaFlow()
    result = await client.run("my_workflow", input_text="Hello")
    print(result)

    # Stream events
    async for event in client.run_stream("my_workflow", input_text="Hello"):
        print(event)

Usage from CLI:
    python -m ollamaflow run my_workflow --input "Hello"
    python -m ollamaflow list
"""

from .client import OllamaFlow, WorkflowResult, RunEvent

__version__ = "0.1.0"
__all__ = ["OllamaFlow", "WorkflowResult", "RunEvent"]
