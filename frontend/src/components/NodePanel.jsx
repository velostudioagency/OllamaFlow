import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronRight, GripVertical, Download, Webhook, Brain, Shield, Wrench, Wand2, Database, GitBranch, Repeat, Link, Timer, FileOutput, Package, Search, Layers, BarChart3, Settings, Send } from 'lucide-react';

const NODE_ICONS = {
  input: Download,
  webhook: Webhook,
  llm: Brain,
  guardrails: Shield,
  tool: Wrench,
  transform: Wand2,
  memory: Database,
  condition: GitBranch,
  switch: GitBranch,
  loop: Repeat,
  merge: Link,
  delay: Timer,
  output: FileOutput,
  variable: Package,
  subworkflow: Layers,
  batch: BarChart3,
  custom: Settings,
  webhook_output: Send,
};

const NODE_COLORS = {
  input: '#3B82F6',
  webhook: '#10B981',
  llm: '#8B5CF6',
  guardrails: '#F43F5E',
  tool: '#F97316',
  transform: '#06B6D4',
  memory: '#22C55E',
  condition: '#EAB308',
  switch: '#F59E0B',
  loop: '#EC4899',
  merge: '#A78BFA',
  delay: '#6366F1',
  output: '#6B7280',
  variable: '#D946EF',
  subworkflow: '#0EA5E9',
  batch: '#F472B6',
  custom: '#A3E635',
  webhook_output: '#F97316',
};

const CATEGORY_ICONS = {
  Trigger: Webhook,
  AI: Brain,
  Tools: Wrench,
  Memory: Database,
  Logic: GitBranch,
  Output: FileOutput,
  Compose: Layers,
};

const NODE_CATEGORIES = [
  {
    name: 'Trigger',
    nodes: [
      { type: 'input', label: 'Input Node', desc: 'Starting point - provides initial input/goal' },
      { type: 'webhook', label: 'Webhook Node', desc: 'Send/receive data via HTTP webhook' },
    ],
  },
  {
    name: 'AI',
    nodes: [
      { type: 'llm', label: 'LLM Node', desc: 'Sends input to an Ollama model' },
      { type: 'guardrails', label: 'Guardrails Node', desc: 'Validate output and route to valid/invalid paths' },
    ],
  },
  {
    name: 'Tools',
    nodes: [
      { type: 'tool', label: 'Tool Node', desc: 'Web search, file I/O, code execution, etc.' },
      { type: 'transform', label: 'Transform Node', desc: 'Regex, case changes, JSON path, templates' },
      { type: 'variable', label: 'Variable Node', desc: 'Store, retrieve, or reuse variables across workflow' },
      { type: 'custom', label: 'Custom Node', desc: 'Write Python code to define custom logic' },
    ],
  },
  {
    name: 'Memory',
    nodes: [
      { type: 'memory', label: 'Memory Node', desc: 'Short-term or long-term agent memory' },
    ],
  },
  {
    name: 'Logic',
    nodes: [
      { type: 'condition', label: 'Condition Node', desc: 'If/else branching logic' },
      { type: 'switch', label: 'Switch Node', desc: 'Multi-way routing based on input' },
      { type: 'loop', label: 'Loop Node', desc: 'Repeat action N times' },
      { type: 'merge', label: 'Merge Node', desc: 'Combine outputs from branches' },
      { type: 'delay', label: 'Delay Node', desc: 'Pause execution for N seconds' },
    ],
  },
  {
    name: 'Compose',
    nodes: [
      { type: 'subworkflow', label: 'Sub-Workflow', desc: 'Nest another workflow inside this node' },
      { type: 'batch', label: 'Batch Node', desc: 'Process lists through a sub-pipeline' },
    ],
  },
  {
    name: 'Output',
    nodes: [
      { type: 'output', label: 'Output Node', desc: 'End of workflow - shows final result' },
      { type: 'webhook_output', label: 'Webhook Output', desc: 'Send workflow output to an external API' },
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
    Compose: true,
    Output: true,
  });
  const [searchQuery, setSearchQuery] = useState('');

  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) return NODE_CATEGORIES;
    const q = searchQuery.toLowerCase();
    return NODE_CATEGORIES.map((cat) => ({
      ...cat,
      nodes: cat.nodes.filter(
        (n) => n.label.toLowerCase().includes(q) || n.desc.toLowerCase().includes(q) || n.type.toLowerCase().includes(q)
      ),
    })).filter((cat) => cat.nodes.length > 0);
  }, [searchQuery]);

  const toggleCategory = (name) => {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-56 bg-[#141414] border-r border-[#333] flex flex-col shrink-0 overflow-y-auto">
      <div className="px-3 py-2 border-b border-[#333]">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search nodes..."
            className="w-full bg-[#0f0f0f] border border-[#333] rounded-lg pl-7 pr-2 py-1.5 text-xs text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>
      <div className="px-4 py-2 border-b border-[#333]">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Nodes</h2>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {filteredCategories.map((cat) => (
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
              <span>{React.createElement(CATEGORY_ICONS[cat.name] || ChevronDown, { className: 'w-3 h-3 text-gray-400' })}</span>
              <span className="font-medium">{cat.name}</span>
              <span className="ml-auto text-[10px] text-gray-600">{cat.nodes.length}</span>
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
                    {(() => {
                      const Icon = NODE_ICONS[node.type];
                      return Icon ? <Icon className="w-3.5 h-3.5 shrink-0" style={{ color: NODE_COLORS[node.type] }} /> : null;
                    })()}
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
