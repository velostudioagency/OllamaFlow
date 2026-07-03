import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { GitBranch } from 'lucide-react';

const ConditionNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const condition = config.condition || 'if output contains error';

  return (
    <div className="min-w-[200px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <GitBranch className="w-3 h-3 text-yellow-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Condition</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-[10px] text-gray-400 truncate max-w-[180px]" title={condition}>
          {condition}
        </p>
        <div className="flex justify-between mt-1.5 px-2">
          <span className="text-[9px] text-green-400 font-medium">True</span>
          <span className="text-[9px] text-red-400 font-medium">False</span>
        </div>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-yellow-500 !border-yellow-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-true"
        style={{ left: '30%' }}
        className="!bg-green-500 !border-green-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-false"
        style={{ left: '70%' }}
        className="!bg-red-500 !border-red-400"
      />
    </div>
  );
});

ConditionNode.displayName = 'ConditionNode';
export default ConditionNode;
