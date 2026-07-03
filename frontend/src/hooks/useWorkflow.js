import { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import {
  addEdge,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import axios from 'axios';
import { showToast } from '../components/Toast';
import { getDefaultConfig, getId, setNodeId } from '../utils/defaults';
import examples from '../utils/examples';

export default function useWorkflow() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const reactFlowInstance = useRef(null);

  const historyRef = useRef([]);
  const historyIndexRef = useRef(-1);
  const skipHistoryRef = useRef(false);

  const pushHistory = useCallback((nodesSnapshot, edgesSnapshot) => {
    if (skipHistoryRef.current) return;
    const entry = {
      nodes: JSON.parse(JSON.stringify(nodesSnapshot)),
      edges: JSON.parse(JSON.stringify(edgesSnapshot)),
    };
    const idx = historyIndexRef.current;
    historyRef.current = historyRef.current.slice(0, idx + 1);
    historyRef.current.push(entry);
    if (historyRef.current.length > 50) {
      historyRef.current.shift();
    }
    historyIndexRef.current = historyRef.current.length - 1;
  }, []);

  const undo = useCallback(() => {
    if (historyIndexRef.current <= 0) return;
    historyIndexRef.current--;
    const entry = historyRef.current[historyIndexRef.current];
    skipHistoryRef.current = true;
    setNodes(entry.nodes);
    setEdges(entry.edges);
    skipHistoryRef.current = false;
  }, [setNodes, setEdges]);

  const redo = useCallback(() => {
    if (historyIndexRef.current >= historyRef.current.length - 1) return;
    historyIndexRef.current++;
    const entry = historyRef.current[historyIndexRef.current];
    skipHistoryRef.current = true;
    setNodes(entry.nodes);
    setEdges(entry.edges);
    skipHistoryRef.current = false;
  }, [setNodes, setEdges]);

  const duplicateNode = useCallback(() => {
    if (!selectedNode) return;
    const node = nodes.find((n) => n.id === selectedNode.id);
    if (!node) return;
    const newNode = {
      id: getId(),
      type: node.type,
      position: { x: node.position.x + 40, y: node.position.y + 40 },
      data: JSON.parse(JSON.stringify(node.data)),
    };
    setNodes((nds) => [...nds, newNode]);
  }, [selectedNode, nodes, setNodes]);

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

  const clearCanvas = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setWorkflowName('Untitled Workflow');
    setNodeId(0);
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
          data: e.data || {},
        })),
      };
      await axios.post('/api/save', { name: workflowName, workflow: workflowData });
      showToast('Workflow saved!', 'success');
    } catch (err) {
      showToast('Failed to save: ' + (err.response?.data?.detail || err.message), 'error');
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
        setNodeId(maxId);
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
          data: e.data || (e.condition ? { condition: e.condition } : {}),
        }));
        setEdges(loadedEdges);
      }
    } catch (err) {
      showToast('Failed to load: ' + (err.response?.data?.detail || err.message), 'error');
    }
  }, [setNodes, setEdges]);

  const loadExample = useCallback(async (exampleName) => {
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
      setNodeId(100);
    }
  }, [setNodes, setEdges]);

  const importFromUrl = useCallback(async () => {
    const url = prompt('Enter workflow URL to import:');
    if (!url) return;
    try {
      const resp = await axios.post('/api/import-url', { url });
      const wf = resp.data.workflow;
      setWorkflowName(resp.data.name || 'Imported Workflow');
      if (wf.nodes) {
        const loadedNodes = wf.nodes.map((n) => ({
          id: n.id,
          type: n.type,
          position: n.position || { x: 0, y: 0 },
          data: n.data || { label: n.type, config: {} },
        }));
        setNodes(loadedNodes);
      }
      if (wf.edges) {
        const loadedEdges = wf.edges.map((e, i) => ({
          id: `imp_edge_${i}`,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle || '',
          targetHandle: e.targetHandle || '',
          type: e.type || 'smoothstep',
          style: { stroke: '#555', strokeWidth: 2 },
          data: e.data || (e.condition ? { condition: e.condition } : {}),
        }));
        setEdges(loadedEdges);
      }
    } catch (err) {
      showToast('Failed to import: ' + (err.response?.data?.detail || err.message), 'error');
    }
  }, [setNodes, setEdges]);

  const exportWorkflow = useCallback(() => {
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
        data: e.data || {},
      })),
    };
    const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflowName.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [nodes, edges, workflowName]);

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

  useEffect(() => {
    if (!skipHistoryRef.current) {
      pushHistory(nodes, edges);
    }
  }, [nodes, edges, pushHistory]);

  return {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    selectedNode,
    setSelectedNode,
    workflowName,
    setWorkflowName,
    saveWorkflow,
    loadWorkflow,
    loadExample,
    clearCanvas,
    undo,
    redo,
    duplicateNode,
    importFromUrl,
    exportWorkflow,
    onConnect,
    onDragOver,
    onDrop,
    onInit,
    onNodeClick,
    onPaneClick,
    updateNodeConfig,
    updateNodeLabel,
    deleteNode,
    onNodesChangeWithState,
    getDefaultConfig,
  };
}
