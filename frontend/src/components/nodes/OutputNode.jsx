import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { FileOutput } from 'lucide-react';

const OutputNode = memo(({ data, selected }) => {
  return (
    <div className="min-w-[160px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <FileOutput className="w-3 h-3 text-gray-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Output</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400 text-center">Final Result</p>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-gray-500 !border-gray-400"
      />
    </div>
  );
});

OutputNode.displayName = 'OutputNode';
export default OutputNode;
