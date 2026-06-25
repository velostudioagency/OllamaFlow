import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Brain } from 'lucide-react';

const LLMNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const model = config.model || 'llama3.1:8b';
  const temperature = config.temperature || 0.7;
  const maxTokens = config.max_tokens || 2000;

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-purple-500" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">LLM</span>
        <Brain className="w-3 h-3 text-purple-400 ml-auto" />
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400 mb-0.5">Model: <span className="text-white">{model}</span></p>
        <p className="text-[10px] text-gray-500">Temp: {temperature} · Max: {maxTokens}</p>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-purple-500 !border-purple-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-purple-500 !border-purple-400"
      />
    </div>
  );
});

LLMNode.displayName = 'LLMNode';
export default LLMNode;
