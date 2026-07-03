import sys
import os
import pytest
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_workflow():
    return {
        "name": "Test Workflow",
        "nodes": [
            {"id": "n1", "type": "input", "config": {"prompt": "Hello world"}},
            {"id": "n2", "type": "output", "config": {}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "", "targetHandle": ""}
        ],
    }


@pytest.fixture
def branching_workflow():
    return {
        "name": "Branching Workflow",
        "nodes": [
            {"id": "n1", "type": "input", "config": {"prompt": "Test input"}},
            {"id": "n2", "type": "condition", "config": {"condition": "if output contains error"}},
            {"id": "n3", "type": "output", "config": {}},
            {"id": "n4", "type": "output", "config": {}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "", "targetHandle": ""},
            {"source": "n2", "target": "n3", "sourceHandle": "handle-true", "targetHandle": ""},
            {"source": "n2", "target": "n4", "sourceHandle": "handle-false", "targetHandle": ""},
        ],
    }


@pytest.fixture
def parallel_workflow():
    return {
        "name": "Parallel Workflow",
        "nodes": [
            {"id": "n1", "type": "input", "config": {"prompt": "Start"}},
            {"id": "n2", "type": "transform", "config": {"transform_type": "uppercase"}},
            {"id": "n3", "type": "transform", "config": {"transform_type": "lowercase"}},
            {"id": "n4", "type": "merge", "config": {"merge_mode": "concat"}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "", "targetHandle": ""},
            {"source": "n1", "target": "n3", "sourceHandle": "", "targetHandle": ""},
            {"source": "n2", "target": "n4", "sourceHandle": "", "targetHandle": ""},
            {"source": "n3", "target": "n4", "sourceHandle": "", "targetHandle": ""},
        ],
    }
