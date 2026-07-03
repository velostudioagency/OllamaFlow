import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Repeat } from 'lucide-react';

const LoopNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const maxIter = config.max_iterations || 5;
  const stopCondition = config.stop_condition || '';

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Repeat className="w-3 h-3 text-pink-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Loop</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-white mb-0.5">🔁 Max: {maxIter} iterations</p>
        {stopCondition && (
          <p className="text-[10px] text-gray-500 truncate" title={stopCondition}>
            Stop: {stopCondition}
          </p>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-pink-500 !border-pink-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-pink-500 !border-pink-400"
      />
    </div>
  );
});

LoopNode.displayName = 'LoopNode';
export default LoopNode;
