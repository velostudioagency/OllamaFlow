import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Link } from 'lucide-react';

const MergeNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const mergeMode = config.merge_mode || 'concat';

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Link className="w-3 h-3 text-violet-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Merge</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400">Mode: <span className="text-white">{mergeMode}</span></p>
        <p className="text-[10px] text-gray-500">Combines multiple inputs</p>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        id="handle-left"
        style={{ left: '30%' }}
        className="!bg-violet-400 !border-violet-300"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="handle-right"
        style={{ left: '70%' }}
        className="!bg-violet-400 !border-violet-300"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-violet-400 !border-violet-300"
      />
    </div>
  );
});

MergeNode.displayName = 'MergeNode';
export default MergeNode;
