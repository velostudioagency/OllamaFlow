import { useState, useCallback, useRef, useMemo } from 'react';

export default function useWebSocket({ nodes, edges, workflowName }) {
  const wsRef = useRef(null);

  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [finalOutput, setFinalOutput] = useState('');
  const [errors, setErrors] = useState([]);
  const [nodeStates, setNodeStates] = useState({});
  const [runDuration, setRunDuration] = useState(null);
  const [streamText, setStreamText] = useState('');
  const [streamingNode, setStreamingNode] = useState('');
  const [tokenUsage, setTokenUsage] = useState(null);

  const runWorkflow = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setLogs([]);
    setFinalOutput('');
    setErrors([]);
    setNodeStates({});
    setRunDuration(null);
    setStreamText('');
    setStreamingNode('');
    const startTime = Date.now();

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
        condition: e.data?.condition || '',
      })),
    };

    try {
      const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/run`);
      wsRef.current = ws;
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
              if (log.node_type === 'llm') {
                setStreamingNode(log.message.split(':')[0] || 'LLM');
              }
            } else if (log.status === 'success') {
              setNodeStates((prev) => ({ ...prev, [log.node_id]: 'success' }));
              if (log.node_type === 'llm') {
                setStreamingNode('');
              }
            } else if (log.status === 'error') {
              setNodeStates((prev) => ({ ...prev, [log.node_id]: 'error' }));
              setStreamingNode('');
            }
          }
        } else if (msg.type === 'stream') {
          setStreamText((prev) => prev + (msg.data.token || ''));
        } else if (msg.type === 'complete') {
          setFinalOutput(msg.data.output || '');
          setErrors(msg.data.errors || []);
          setRunDuration(((Date.now() - startTime) / 1000).toFixed(1));
          setTokenUsage(msg.data.token_usage || null);
          setIsRunning(false);
          setNodeStates({});
          setStreamingNode('');
          wsRef.current = null;
          ws.close();
        } else if (msg.type === 'error') {
          setErrors([msg.message]);
          setRunDuration(((Date.now() - startTime) / 1000).toFixed(1));
          setIsRunning(false);
          setStreamingNode('');
          wsRef.current = null;
          ws.close();
        }
      };
      ws.onerror = () => {
        setErrors(['WebSocket connection failed. Is the backend running?']);
        setRunDuration(((Date.now() - startTime) / 1000).toFixed(1));
        setIsRunning(false);
      };
      ws.onclose = () => {
        wsRef.current = null;
        setIsRunning(false);
      };
    } catch (err) {
      setErrors([`Connection error: ${err.message}`]);
      setRunDuration(((Date.now() - startTime) / 1000).toFixed(1));
      setIsRunning(false);
    }
  }, [nodes, edges, workflowName, isRunning]);

  const stopWorkflow = useCallback(() => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }));
      ws.close();
    }
    wsRef.current = null;
    setIsRunning(false);
    setNodeStates({});
  }, []);

  const workflowData = useMemo(() => ({
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
      condition: e.data?.condition || '',
    })),
  }), [nodes, edges, workflowName]);

  return {
    runWorkflow,
    stopWorkflow,
    isRunning,
    logs,
    setLogs,
    finalOutput,
    setFinalOutput,
    errors,
    setErrors,
    nodeStates,
    setNodeStates,
    runDuration,
    setRunDuration,
    streamText,
    streamingNode,
    tokenUsage,
    workflowData,
  };
}
