import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Database } from 'lucide-react';

const MemoryNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const namespace = config.namespace || 'default';
  const memoryType = config.memory_type || 'long_term';
  const action = config.action || 'remember';

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Database className="w-3 h-3 text-green-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Memory</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-white mb-0.5">
          {action === 'remember' ? '💾' : action === 'recall' ? '📥' : action === 'search' ? '🔍' : '🗑️'} {action}
        </p>
        <p className="text-[10px] text-gray-500">ns: {namespace} · {memoryType}</p>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-green-500 !border-green-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-green-500 !border-green-400"
      />
    </div>
  );
});

MemoryNode.displayName = 'MemoryNode';
export default MemoryNode;
