import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Bot } from 'lucide-react';

const AgentNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const model = config.model || 'llama3.1:8b';
  const tools = config.tools || [];
  const maxSteps = config.max_steps || 10;
  const hasMemory = config.memory || false;

  return (
    <div className="min-w-[200px]">
      <div className="bg-gradient-to-r from-red-900/40 to-red-800/20 rounded-t-lg px-3 py-1.5 border-b border-red-900/50 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-red-500" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Agent</span>
        <Bot className="w-3 h-3 text-red-400 ml-auto" />
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg border border-red-900/30">
        <p className="text-xs text-white mb-1">🤖 {model}</p>
        <p className="text-[10px] text-gray-500 mb-0.5">Steps: {maxSteps}</p>
        {tools.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {tools.map((t) => (
              <span key={t} className="px-1.5 py-0.5 bg-orange-900/30 text-orange-300 rounded text-[9px]">
                {t}
              </span>
            ))}
          </div>
        )}
        {hasMemory && (
          <span className="inline-block mt-1 px-1.5 py-0.5 bg-green-900/30 text-green-300 rounded text-[9px]">
            memory
          </span>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-red-500 !border-red-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-red-500 !border-red-400"
      />
    </div>
  );
});

AgentNode.displayName = 'AgentNode';
export default AgentNode;
