import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Download } from 'lucide-react';

const InputNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const inputType = config.input_type || 'text';
  const prompt = config.prompt || 'Enter your goal...';

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Download className="w-3 h-3 text-blue-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Input</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400 mb-1">Type: <span className="text-white">{inputType}</span></p>
        <p className="text-[10px] text-gray-500 truncate max-w-[160px]" title={prompt}>
          {prompt || 'No prompt set'}
        </p>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-blue-500 !border-blue-400"
      />
    </div>
  );
});

InputNode.displayName = 'InputNode';
export default InputNode;
