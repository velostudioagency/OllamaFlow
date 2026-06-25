import React, { useState } from 'react';
import { ChevronDown, ChevronRight, GripVertical } from 'lucide-react';

const NODE_CATEGORIES = [
  {
    name: 'Trigger',
    icon: '🔵',
    nodes: [
      { type: 'input', label: 'Input Node', desc: 'Starting point - provides initial input/goal', color: '#3B82F6' },
    ],
  },
  {
    name: 'AI',
    icon: '🟣',
    nodes: [
      { type: 'llm', label: 'LLM Node', desc: 'Sends input to an Ollama model', color: '#8B5CF6' },
      { type: 'agent', label: 'Agent Node', desc: 'Full autonomous agent with tools + reasoning', color: '#EF4444' },
    ],
  },
  {
    name: 'Tools',
    icon: '🟠',
    nodes: [
      { type: 'tool', label: 'Tool Node', desc: 'Web search, file I/O, code execution, etc.', color: '#F97316' },
    ],
  },
  {
    name: 'Memory',
    icon: '🟢',
    nodes: [
      { type: 'memory', label: 'Memory Node', desc: 'Short-term or long-term agent memory', color: '#22C55E' },
    ],
  },
  {
    name: 'Logic',
    icon: '🟡',
    nodes: [
      { type: 'condition', label: 'Condition Node', desc: 'If/else branching logic', color: '#EAB308' },
      { type: 'loop', label: 'Loop Node', desc: 'Repeat action N times', color: '#EC4899' },
    ],
  },
  {
    name: 'Output',
    icon: '⬛',
    nodes: [
      { type: 'output', label: 'Output Node', desc: 'End of workflow - shows final result', color: '#6B7280' },
    ],
  },
];

export default function NodePanel() {
  const [expanded, setExpanded] = useState({
    Trigger: true,
    AI: true,
    Tools: true,
    Memory: true,
    Logic: true,
    Output: true,
  });

  const toggleCategory = (name) => {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-56 bg-[#141414] border-r border-[#333] flex flex-col shrink-0 overflow-y-auto">
      <div className="px-4 py-3 border-b border-[#333]">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Nodes</h2>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {NODE_CATEGORIES.map((cat) => (
          <div key={cat.name} className="mb-1">
            <button
              onClick={() => toggleCategory(cat.name)}
              className="w-full flex items-center gap-2 px-4 py-2 text-xs text-gray-400 hover:text-gray-200 hover:bg-[#1a1a1a] transition"
            >
              {expanded[cat.name] ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
              <span>{cat.icon}</span>
              <span className="font-medium">{cat.name}</span>
            </button>
            {expanded[cat.name] && (
              <div className="py-1">
                {cat.nodes.map((node) => (
                  <div
                    key={node.type}
                    draggable
                    onDragStart={(e) => onDragStart(e, node.type)}
                    className="group mx-2 mb-1 flex items-center gap-2 px-3 py-2 rounded-lg cursor-grab hover:bg-[#222] transition border border-transparent hover:border-[#444]"
                    title={node.desc}
                  >
                    <GripVertical className="w-3 h-3 text-gray-600 group-hover:text-gray-400 shrink-0" />
                    <div
                      className="w-2.5 h-2.5 rounded-sm shrink-0"
                      style={{ backgroundColor: node.color }}
                    />
                    <span className="text-xs text-gray-300 group-hover:text-white truncate">
                      {node.label}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
