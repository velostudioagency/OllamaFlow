import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Wand2 } from 'lucide-react';

const TransformNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const transformType = config.transform_type || 'trim';

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Wand2 className="w-3 h-3 text-cyan-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Transform</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400">Type: <span className="text-white">{transformType}</span></p>
        {config.pattern && (
          <p className="text-[10px] text-gray-500 truncate max-w-[160px]" title={config.pattern}>
            Pattern: {config.pattern}
          </p>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-cyan-500 !border-cyan-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-cyan-500 !border-cyan-400"
      />
    </div>
  );
});

TransformNode.displayName = 'TransformNode';
export default TransformNode;
