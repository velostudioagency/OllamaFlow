import React, { useState, useRef, useEffect } from 'react';
import { Play, Square, Save, FolderOpen, Plus, Zap, ChevronDown, Check, X, Settings as SettingsIcon } from 'lucide-react';
import axios from 'axios';

export default function Toolbar({
  workflowName,
  onNameChange,
  onRun,
  onStop,
  onSave,
  onLoad,
  onClear,
  onLoadExample,
  isRunning,
  ollamaStatus,
  onOpenSettings,
}) {
  const [showExamples, setShowExamples] = useState(false);
  const [showLoad, setShowLoad] = useState(false);
  const [workflows, setWorkflows] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const fetchWorkflows = async () => {
    try {
      const resp = await axios.get('/api/workflows');
      setWorkflows(resp.data.workflows || []);
    } catch (err) {
      console.error('Failed to fetch workflows');
    }
  };

  const handleLoadClick = () => {
    fetchWorkflows();
    setShowLoad(!showLoad);
    setShowExamples(false);
  };

  return (
    <div className="h-12 bg-[#1a1a1a] border-b border-[#333] flex items-center px-4 shrink-0">
      <div className="flex items-center gap-2 mr-6">
        <Zap className="w-5 h-5 text-yellow-400" />
        <span className="font-bold text-white text-sm tracking-wide">OllamaFlow</span>
      </div>

      <div className="flex-1 flex items-center justify-center">
        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            value={workflowName}
            onChange={(e) => onNameChange(e.target.value)}
            onBlur={() => setIsEditing(false)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') setIsEditing(false);
            }}
            className="bg-[#0f0f0f] border border-[#555] rounded px-3 py-1 text-sm text-white text-center w-64 focus:outline-none focus:border-blue-500"
          />
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="text-sm text-gray-300 hover:text-white px-3 py-1 rounded hover:bg-[#333] transition"
          >
            {workflowName}
          </button>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onClear}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-[#333] rounded transition"
          title="New Workflow"
        >
          <Plus className="w-3.5 h-3.5" />
          New
        </button>

        <button
          onClick={onSave}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-[#333] rounded transition"
          title="Save Workflow"
        >
          <Save className="w-3.5 h-3.5" />
          Save
        </button>

        <div className="relative">
          <button
            onClick={handleLoadClick}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-[#333] rounded transition"
            title="Load Workflow"
          >
            <FolderOpen className="w-3.5 h-3.5" />
            Load
          </button>
          {showLoad && (
            <div className="absolute top-full right-0 mt-1 bg-[#1a1a1a] border border-[#333] rounded-lg shadow-xl z-50 w-64 max-h-64 overflow-y-auto">
              {workflows.length === 0 ? (
                <div className="px-4 py-3 text-xs text-gray-500">No saved workflows</div>
              ) : (
                workflows.map((wf) => (
                  <button
                    key={wf.name}
                    onClick={() => {
                      onLoad(wf.name);
                      setShowLoad(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-[#333] hover:text-white transition flex items-center justify-between"
                  >
                    <span>{wf.name}</span>
                    <span className="text-xs text-gray-600">{wf.node_count} nodes</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        <div className="relative">
          <button
            onClick={() => {
              setShowExamples(!showExamples);
              setShowLoad(false);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-[#333] rounded transition"
          >
            Examples
            <ChevronDown className="w-3 h-3" />
          </button>
          {showExamples && (
            <div className="absolute top-full right-0 mt-1 bg-[#1a1a1a] border border-[#333] rounded-lg shadow-xl z-50 w-64">
              {['Web Research Agent', 'File Summarizer', 'Multi-Step Research Report'].map((name) => (
                <button
                  key={name}
                  onClick={() => {
                    onLoadExample(name);
                    setShowExamples(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-[#333] hover:text-white transition"
                >
                  {name}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="w-px h-6 bg-[#333] mx-1" />

        <button
          onClick={onOpenSettings}
          className="p-1.5 text-gray-400 hover:text-white hover:bg-[#333] rounded transition"
          title="Settings"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>

        {isRunning ? (
          <button
            onClick={onStop}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium bg-red-600 hover:bg-red-700 text-white rounded transition"
          >
            <Square className="w-3.5 h-3.5" />
            Stop
          </button>
        ) : (
          <button
            onClick={onRun}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium bg-green-600 hover:bg-green-700 text-white rounded transition"
          >
            <Play className="w-3.5 h-3.5" />
            Run
          </button>
        )}

        <div className="flex items-center gap-1.5 ml-2" title={`Ollama: ${ollamaStatus}`}>
          <div className={`w-2 h-2 rounded-full ${ollamaStatus === 'connected' ? 'bg-green-500' : ollamaStatus === 'checking' ? 'bg-yellow-500' : 'bg-red-500'}`} />
        </div>
      </div>
    </div>
  );
}
