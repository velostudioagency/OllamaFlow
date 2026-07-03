import pytest
import asyncio
import json


def test_build_graph(sample_workflow):
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    graph = runner._build_graph(sample_workflow)
    assert "n1" in graph["nodes"]
    assert "n2" in graph["nodes"]
    assert graph["in_degree"]["n1"] == 0
    assert graph["in_degree"]["n2"] == 1
    assert "n1" in graph["start_nodes"]


def test_build_graph_branching(branching_workflow):
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    graph = runner._build_graph(branching_workflow)
    assert len(graph["edges"]) == 3
    assert graph["in_degree"]["n1"] == 0


def test_build_graph_parallel(parallel_workflow):
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    graph = runner._build_graph(parallel_workflow)
    assert graph["in_degree"]["n1"] == 0
    assert graph["in_degree"]["n2"] == 1
    assert graph["in_degree"]["n3"] == 1
    assert graph["in_degree"]["n4"] == 2


def test_get_next_nodes_condition_true():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    graph = runner._build_graph({
        "nodes": [
            {"id": "n1", "type": "condition"},
            {"id": "n2", "type": "output"},
            {"id": "n3", "type": "output"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "handle-true"},
            {"source": "n1", "target": "n3", "sourceHandle": "handle-false"},
        ]
    })
    next_nodes = runner._get_next_nodes("n1", graph, branch="true")
    assert "n2" in next_nodes
    assert "n3" not in next_nodes


def test_get_next_nodes_condition_false():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    graph = runner._build_graph({
        "nodes": [
            {"id": "n1", "type": "condition"},
            {"id": "n2", "type": "output"},
            {"id": "n3", "type": "output"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "handle-true"},
            {"source": "n1", "target": "n3", "sourceHandle": "handle-false"},
        ]
    })
    next_nodes = runner._get_next_nodes("n1", graph, branch="false")
    assert "n3" in next_nodes
    assert "n2" not in next_nodes


def test_get_next_nodes_no_branch():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    graph = runner._build_graph({
        "nodes": [
            {"id": "n1", "type": "llm"},
            {"id": "n2", "type": "output"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
        ]
    })
    next_nodes = runner._get_next_nodes("n1", graph)
    assert "n2" in next_nodes


def test_get_next_nodes_edge_condition():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    runner.context = {"current_input": "test"}
    graph = runner._build_graph({
        "nodes": [
            {"id": "n1", "type": "llm"},
            {"id": "n2", "type": "output"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "condition": "True"},
        ]
    })
    next_nodes = runner._get_next_nodes("n1", graph)
    assert "n2" in next_nodes


@pytest.mark.asyncio
async def test_run_simple_workflow(sample_workflow):
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    result = await runner.run(sample_workflow)
    assert result["status"] == "completed"
    assert result["output"] == "Hello world"
    assert len(result["logs"]) > 0


@pytest.mark.asyncio
async def test_run_empty_workflow():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    result = await runner.run({"name": "Empty", "nodes": [], "edges": []})
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_run_no_start_node():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    result = await runner.run({
        "name": "No Start",
        "nodes": [{"id": "n1", "type": "llm", "config": {}}],
        "edges": []
    })
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_runner_stop():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    runner.should_stop = True
    result = await runner.run({
        "name": "Stopped",
        "nodes": [{"id": "n1", "type": "input", "config": {"prompt": "test"}}],
        "edges": []
    })
    assert runner.should_stop is True


def test_runner_reset():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    runner.context = {"test": "value"}
    runner.logs = [{"msg": "test"}]
    runner.is_running = True
    runner.should_stop = True
    runner.reset()
    assert runner.context == {}
    assert runner.logs == []
    assert runner.is_running is False
    assert runner.should_stop is False


@pytest.mark.asyncio
async def test_run_transform_workflow():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    workflow = {
        "name": "Transform Test",
        "nodes": [
            {"id": "n1", "type": "input", "config": {"prompt": "hello"}},
            {"id": "n2", "type": "transform", "config": {"transform_type": "uppercase"}},
            {"id": "n3", "type": "output", "config": {}},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
        ]
    }
    result = await runner.run(workflow)
    assert result["status"] == "completed"
    assert result["output"] == "HELLO"


@pytest.mark.asyncio
async def test_run_condition_true():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    workflow = {
        "name": "Condition True",
        "nodes": [
            {"id": "n1", "type": "input", "config": {"prompt": "error occurred"}},
            {"id": "n2", "type": "condition", "config": {"condition": "if output contains error"}},
            {"id": "n3", "type": "output", "config": {}},
            {"id": "n4", "type": "output", "config": {}},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3", "sourceHandle": "handle-true"},
            {"source": "n2", "target": "n4", "sourceHandle": "handle-false"},
        ]
    }
    result = await runner.run(workflow)
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_run_condition_false():
    from agent_runner import WorkflowRunner
    runner = WorkflowRunner()
    workflow = {
        "name": "Condition False",
        "nodes": [
            {"id": "n1", "type": "input", "config": {"prompt": "everything is fine"}},
            {"id": "n2", "type": "condition", "config": {"condition": "if output contains error"}},
            {"id": "n3", "type": "output", "config": {}},
            {"id": "n4", "type": "output", "config": {}},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3", "sourceHandle": "handle-true"},
            {"source": "n2", "target": "n4", "sourceHandle": "handle-false"},
        ]
    }
    result = await runner.run(workflow)
    assert result["status"] == "completed"
