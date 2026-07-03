import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactFlow, { Controls, MiniMap, Background } from 'reactflow';
import 'reactflow/dist/style.css';
import Toolbar from './components/Toolbar';
import NodePanel from './components/NodePanel';
import ConfigPanel from './components/ConfigPanel';
import OutputPanel from './components/OutputPanel';
import Settings from './components/Settings';
import ChatPanel from './components/ChatPanel';
import ExecutionHistory from './components/ExecutionHistory';
import ToastContainer from './components/Toast';
import ShortcutModal from './components/ShortcutModal';
import useWorkflow from './hooks/useWorkflow';
import useWebSocket from './hooks/useWebSocket';
import { nodeTypes, NODE_COLORS } from './utils/defaults';

function FlowCanvas() {
  const workflow = useWorkflow();
  const ws = useWebSocket({
    nodes: workflow.nodes,
    edges: workflow.edges,
    workflowName: workflow.workflowName,
  });

  const [ollamaStatus, setOllamaStatus] = useState('checking');
  const [showOutput, setShowOutput] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      if (showChat) return;
      const isInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT';
      if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        workflow.saveWorkflow();
      } else if (e.key === 'z' && (e.ctrlKey || e.metaKey) && !e.shiftKey) {
        e.preventDefault();
        workflow.undo();
      } else if ((e.key === 'y' && (e.ctrlKey || e.metaKey)) || (e.key === 'z' && (e.ctrlKey || e.metaKey) && e.shiftKey)) {
        e.preventDefault();
        workflow.redo();
      } else if (e.key === 'd' && (e.ctrlKey || e.metaKey) && !isInput) {
        e.preventDefault();
        workflow.duplicateNode();
      } else if (e.key === '?' && !isInput) {
        e.preventDefault();
        setShowShortcuts((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [workflow.saveWorkflow, workflow.undo, workflow.redo, workflow.duplicateNode, showChat]);

  const handleRun = useCallback(() => {
    setShowOutput(true);
    ws.runWorkflow();
  }, [ws.runWorkflow]);

  const styledNodes = useMemo(() => {
    return workflow.nodes.map((n) => ({
      ...n,
      className: ws.nodeStates[n.id] || '',
    }));
  }, [workflow.nodes, ws.nodeStates]);

  return (
    <div className="h-screen flex flex-col bg-[#0f0f0f]">
      <Toolbar
        workflowName={workflow.workflowName}
        onNameChange={workflow.setWorkflowName}
        onRun={handleRun}
        onStop={ws.stopWorkflow}
        onSave={workflow.saveWorkflow}
        onLoad={workflow.loadWorkflow}
        onClear={workflow.clearCanvas}
        onLoadExample={workflow.loadExample}
        isRunning={ws.isRunning}
        ollamaStatus={ollamaStatus}
        onOpenSettings={() => setShowSettings(true)}
        showChat={showChat}
        onToggleChat={() => setShowChat(!showChat)}
        onImportUrl={workflow.importFromUrl}
        onExport={workflow.exportWorkflow}
        onShowHistory={() => setShowHistory(true)}
      />
      <div className="flex flex-1 overflow-hidden">
        {showChat ? (
          <ChatPanel workflow={ws.workflowData} />
        ) : (
          <>
            <NodePanel />
            <div className="flex-1 relative">
              <ReactFlow
                nodes={styledNodes}
                edges={workflow.edges}
                onNodesChange={workflow.onNodesChangeWithState}
                onEdgesChange={workflow.onEdgesChange}
                onConnect={workflow.onConnect}
                onInit={workflow.onInit}
                onDrop={workflow.onDrop}
                onDragOver={workflow.onDragOver}
                onNodeClick={workflow.onNodeClick}
                onPaneClick={workflow.onPaneClick}
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
            {workflow.selectedNode && (
              <ConfigPanel
                node={workflow.selectedNode}
                onUpdateConfig={workflow.updateNodeConfig}
                onUpdateLabel={workflow.updateNodeLabel}
                onDelete={workflow.deleteNode}
                onClose={() => workflow.setSelectedNode(null)}
              />
            )}
          </>
        )}
      </div>
      {showOutput && (
        <OutputPanel
          logs={ws.logs}
          finalOutput={ws.finalOutput}
          errors={ws.errors}
          runDuration={ws.runDuration}
          streamText={ws.streamText}
          streamingNode={ws.streamingNode}
          isRunning={ws.isRunning}
          onClose={() => setShowOutput(false)}
          tokenUsage={ws.tokenUsage}
        />
      )}
      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
      {showHistory && (
        <ExecutionHistory onClose={() => setShowHistory(false)} />
      )}
      {showShortcuts && (
        <ShortcutModal onClose={() => setShowShortcuts(false)} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <FlowCanvas />
      <ToastContainer />
    </ReactFlowProvider>
  );
}
