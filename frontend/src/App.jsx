import React, { useState, useCallback, useRef, useMemo } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import Toolbar from './components/Toolbar';
import NodePanel from './components/NodePanel';
import ConfigPanel from './components/ConfigPanel';
import OutputPanel from './components/OutputPanel';
import LLMNode from './components/nodes/LLMNode';
import ToolNode from './components/nodes/ToolNode';
import MemoryNode from './components/nodes/MemoryNode';
import InputNode from './components/nodes/InputNode';
import OutputNodeComp from './components/nodes/OutputNode';
import ConditionNode from './components/nodes/ConditionNode';
import LoopNode from './components/nodes/LoopNode';
import AgentNode from './components/nodes/AgentNode';

const nodeTypes = {
  input: InputNode,
  llm: LLMNode,
  tool: ToolNode,
  memory: MemoryNode,
  condition: ConditionNode,
  loop: LoopNode,
  agent: AgentNode,
  output: OutputNodeComp,
};

const NODE_COLORS = {
  input: '#3B82F6',
  llm: '#8B5CF6',
  tool: '#F97316',
  memory: '#22C55E',
  condition: '#EAB308',
  loop: '#EC4899',
  agent: '#EF4444',
  output: '#6B7280',
};

let nodeId = 0;
const getId = () => `node_${++nodeId}_${Date.now()}`;

function FlowCanvas() {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [finalOutput, setFinalOutput] = useState('');
  const [errors, setErrors] = useState([]);
  const [ollamaStatus, setOllamaStatus] = useState('checking');
  const [showOutput, setShowOutput] = useState(false);
  const [nodeStates, setNodeStates] = useState({});
  const reactFlowInstance = useRef(null);

  const onConnect = useCallback(
    (params) => {
      const edge = {
        ...params,
        type: 'smoothstep',
        animated: false,
        style: { stroke: '#555', strokeWidth: 2 },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow-type');
      const category = event.dataTransfer.getData('application/reactflow-category');
      if (!type || !reactFlowInstance.current) return;
      const position = reactFlowInstance.current.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      const newNode = {
        id: getId(),
        type,
        position,
        data: {
          label: `${type.charAt(0).toUpperCase() + type.slice(1)} Node`,
          config: getDefaultConfig(type),
        },
      };
      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes]
  );

  const onInit = useCallback((instance) => {
    reactFlowInstance.current = instance;
  }, []);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const updateNodeConfig = useCallback(
    (nodeId, config) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, config: { ...n.data.config, ...config } } }
            : n
        )
      );
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode((prev) => ({
          ...prev,
          data: { ...prev.data, config: { ...prev.data.config, ...config } },
        }));
      }
    },
    [setNodes, selectedNode]
  );

  const updateNodeLabel = useCallback(
    (nodeId, label) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId ? { ...n, data: { ...n.data, label } } : n
        )
      );
    },
    [setNodes]
  );

  const deleteNode = useCallback(
    (nodeId) => {
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode(null);
      }
    },
    [setNodes, setEdges, selectedNode]
  );

  const runWorkflow = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setLogs([]);
    setFinalOutput('');
    setErrors([]);
    setShowOutput(true);
    setNodeStates({});

    const workflowData = {
      name: workflowName,
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type,
        config: n.data.config || {},
      })),
      edges: edges.map((e) => ({
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle || '',
        targetHandle: e.targetHandle || '',
      })),
    };

    try {
      const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/run`);
      ws.onopen = () => {
        ws.send(JSON.stringify(workflowData));
      };
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'log') {
          const log = msg.data;
          setLogs((prev) => [...prev, log]);
          if (log.node_id) {
            if (log.status === 'running') {
              setNodeStates((prev) => ({ ...prev, [log.node_id]: 'running' }));
            } else if (log.status === 'success') {
              setNodeStates((prev) => ({ ...prev, [log.node_id]: 'success' }));
            } else if (log.status === 'error') {
              setNodeStates((prev) => ({ ...prev, [log.node_id]: 'error' }));
            }
          }
        } else if (msg.type === 'complete') {
          setFinalOutput(msg.data.output || '');
          setErrors(msg.data.errors || []);
          setIsRunning(false);
          setNodeStates({});
          ws.close();
        } else if (msg.type === 'error') {
          setErrors([msg.message]);
          setIsRunning(false);
          ws.close();
        }
      };
      ws.onerror = () => {
        setErrors(['WebSocket connection failed. Is the backend running?']);
        setIsRunning(false);
      };
      ws.onclose = () => {
        setIsRunning(false);
      };
    } catch (err) {
      setErrors([`Connection error: ${err.message}`]);
      setIsRunning(false);
    }
  }, [nodes, edges, workflowName, isRunning]);

  const stopWorkflow = useCallback(() => {
    setIsRunning(false);
    setNodeStates({});
  }, []);

  const clearCanvas = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setLogs([]);
    setFinalOutput('');
    setErrors([]);
    setWorkflowName('Untitled Workflow');
    nodeId = 0;
  }, [setNodes, setEdges]);

  const saveWorkflow = useCallback(async () => {
    try {
      const workflowData = {
        name: workflowName,
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type,
          position: n.position,
          data: n.data,
        })),
        edges: edges.map((e) => ({
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle || '',
          targetHandle: e.targetHandle || '',
          type: e.type,
        })),
      };
      await axios.post('/api/save', { name: workflowName, workflow: workflowData });
      alert('Workflow saved!');
    } catch (err) {
      alert('Failed to save: ' + (err.response?.data?.detail || err.message));
    }
  }, [nodes, edges, workflowName]);

  const loadWorkflow = useCallback(async (name) => {
    try {
      const resp = await axios.get(`/api/load/${encodeURIComponent(name)}`);
      const wf = resp.data.workflow;
      setWorkflowName(wf.name || name);
      if (wf.nodes) {
        const loadedNodes = wf.nodes.map((n) => ({
          id: n.id,
          type: n.type,
          position: n.position || { x: 0, y: 0 },
          data: n.data || { label: n.type, config: {} },
        }));
        setNodes(loadedNodes);
        const maxId = loadedNodes.reduce((max, n) => {
          const num = parseInt(n.id.split('_')[1]) || 0;
          return num > max ? num : max;
        }, 0);
        nodeId = maxId;
      }
      if (wf.edges) {
        const loadedEdges = wf.edges.map((e, i) => ({
          id: `edge_${i}`,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle || '',
          targetHandle: e.targetHandle || '',
          type: e.type || 'smoothstep',
          style: { stroke: '#555', strokeWidth: 2 },
        }));
        setEdges(loadedEdges);
      }
    } catch (err) {
      alert('Failed to load: ' + (err.response?.data?.detail || err.message));
    }
  }, [setNodes, setEdges]);

  const loadExample = useCallback(async (exampleName) => {
    const examples = {
      'Web Research Agent': {
        name: 'Web Research Agent',
        nodes: [
          { id: 'ex1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input', config: { prompt: 'Research hotels in Blantyre, Malawi', input_type: 'text' } } },
          { id: 'ex2', type: 'agent', position: { x: 350, y: 200 }, data: { label: 'Research Agent', config: { model: 'llama3.1:8b', tools: ['web_search'], system_prompt: 'You are a research assistant. Search the web and compile information.', max_steps: 5, memory: false } } },
          { id: 'ex3', type: 'output', position: { x: 700, y: 200 }, data: { label: 'Output', config: {} } },
        ],
        edges: [
          { source: 'ex1', target: 'ex2' },
          { source: 'ex2', target: 'ex3' },
        ],
      },
      'File Summarizer': {
        name: 'File Summarizer',
        nodes: [
          { id: 'fs1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input', config: { prompt: 'Summarize the document', input_type: 'text' } } },
          { id: 'fs2', type: 'tool', position: { x: 350, y: 200 }, data: { label: 'Read File', config: { tool_name: 'read_file', params: { file_path: 'document.txt' } } } },
          { id: 'fs3', type: 'llm', position: { x: 650, y: 200 }, data: { label: 'Summarizer', config: { model: 'llama3.1:8b', system_prompt: 'Summarize the following document concisely.', temperature: 0.3, max_tokens: 1000 } } },
          { id: 'fs4', type: 'output', position: { x: 950, y: 200 }, data: { label: 'Output', config: {} } },
        ],
        edges: [
          { source: 'fs1', target: 'fs2' },
          { source: 'fs2', target: 'fs3' },
          { source: 'fs3', target: 'fs4' },
        ],
      },
      'Multi-Step Research Report': {
        name: 'Multi-Step Research Report',
        nodes: [
          { id: 'ms1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input', config: { prompt: 'Write a report on renewable energy trends', input_type: 'text' } } },
          { id: 'ms2', type: 'agent', position: { x: 350, y: 200 }, data: { label: 'Research Agent', config: { model: 'llama3.1:8b', tools: ['web_search'], system_prompt: 'Research the topic thoroughly.', max_steps: 8, memory: false } } },
          { id: 'ms3', type: 'llm', position: { x: 650, y: 200 }, data: { label: 'Report Writer', config: { model: 'llama3.1:8b', system_prompt: 'Write a detailed, well-structured report based on the research.', temperature: 0.5, max_tokens: 3000 } } },
          { id: 'ms4', type: 'tool', position: { x: 950, y: 200 }, data: { label: 'Save Report', config: { tool_name: 'write_file', params: { file_path: 'report.txt' } } } },
          { id: 'ms5', type: 'output', position: { x: 1250, y: 200 }, data: { label: 'Output', config: {} } },
        ],
        edges: [
          { source: 'ms1', target: 'ms2' },
          { source: 'ms2', target: 'ms3' },
          { source: 'ms3', target: 'ms4' },
          { source: 'ms4', target: 'ms5' },
        ],
      },
    };
    const ex = examples[exampleName];
    if (ex) {
      setWorkflowName(ex.name);
      setNodes(ex.nodes);
      setEdges(ex.edges.map((e, i) => ({
        id: `ex_edge_${i}`,
        ...e,
        type: 'smoothstep',
        style: { stroke: '#555', strokeWidth: 2 },
      })));
      nodeId = 100;
    }
  }, [setNodes, setEdges]);

  const onNodesChangeWithState = useCallback(
    (changes) => {
      onNodesChange(changes);
      for (const change of changes) {
        if (change.type === 'select' && change.selected) {
          const node = nodes.find((n) => n.id === change.id);
          if (node) setSelectedNode(node);
        }
      }
    },
    [onNodesChange, nodes]
  );

  const styledNodes = useMemo(() => {
    return nodes.map((n) => ({
      ...n,
      className: nodeStates[n.id] || '',
    }));
  }, [nodes, nodeStates]);

  return (
    <div className="h-screen flex flex-col bg-[#0f0f0f]">
      <Toolbar
        workflowName={workflowName}
        onNameChange={setWorkflowName}
        onRun={runWorkflow}
        onStop={stopWorkflow}
        onSave={saveWorkflow}
        onLoad={loadWorkflow}
        onClear={clearCanvas}
        onLoadExample={loadExample}
        isRunning={isRunning}
        ollamaStatus={ollamaStatus}
      />
      <div className="flex flex-1 overflow-hidden">
        <NodePanel />
        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={styledNodes}
            edges={edges}
            onNodesChange={onNodesChangeWithState}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={onInit}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
            deleteKeyCode="Delete"
            multiSelectionKeyCode="Shift"
            defaultEdgeOptions={{
              type: 'smoothstep',
              style: { stroke: '#555', strokeWidth: 2 },
            }}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#333" gap={20} size={1} />
            <Controls className="!bg-[#1a1a1a] !border-[#333] !rounded-lg" />
            <MiniMap
              nodeColor={(n) => NODE_COLORS[n.type] || '#666'}
              className="!bg-[#1a1a1a] !border-[#333]"
              maskColor="rgba(0,0,0,0.5)"
            />
          </ReactFlow>
        </div>
        {selectedNode && (
          <ConfigPanel
            node={selectedNode}
            onUpdateConfig={updateNodeConfig}
            onUpdateLabel={updateNodeLabel}
            onDelete={deleteNode}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </div>
      {showOutput && (
        <OutputPanel
          logs={logs}
          finalOutput={finalOutput}
          errors={errors}
          onClose={() => setShowOutput(false)}
        />
      )}
    </div>
  );
}

function getDefaultConfig(type) {
  const defaults = {
    input: { prompt: '', input_type: 'text', file_path: '' },
    llm: { model: 'llama3.1:8b', system_prompt: 'You are a helpful assistant.', temperature: 0.7, max_tokens: 2000 },
    tool: { tool_name: 'web_search', params: {} },
    memory: { namespace: 'default', memory_type: 'long_term', action: 'remember', search_query: '' },
    condition: { condition: 'if output contains error' },
    loop: { max_iterations: 5, stop_condition: '' },
    agent: { model: 'llama3.1:8b', tools: [], system_prompt: 'You are a helpful AI agent.', max_steps: 10, memory: false },
    output: {},
  };
  return defaults[type] || {};
}

export default function App() {
  return (
    <ReactFlowProvider>
      <FlowCanvas />
    </ReactFlowProvider>
  );
}
