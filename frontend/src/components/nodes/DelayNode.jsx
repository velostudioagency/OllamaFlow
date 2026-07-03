import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Timer } from 'lucide-react';

const DelayNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const seconds = config.delay_seconds || 5;

  return (
    <div className="min-w-[160px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Timer className="w-3 h-3 text-indigo-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Delay</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400">Wait: <span className="text-white">{seconds}s</span></p>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-indigo-500 !border-indigo-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-indigo-500 !border-indigo-400"
      />
    </div>
  );
});

DelayNode.displayName = 'DelayNode';
export default DelayNode;
