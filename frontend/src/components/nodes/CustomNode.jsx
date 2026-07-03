import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Settings } from 'lucide-react';

const CustomNodeComp = memo(({ data, selected }) => {
  const config = data.config || {};
  const handlerName = config.handler_name || 'process';
  const hasCode = config.custom_code && config.custom_code.trim().length > 0;

  return (
    <div className="min-w-[160px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Settings className="w-3 h-3 text-lime-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Custom</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-[10px] text-gray-400 truncate">
          {hasCode ? `def ${handlerName}()` : 'No code defined'}
        </p>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-lime-900/40 text-lime-300 font-medium">
            Python
          </span>
        </div>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-lime-500 !border-lime-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-lime-500 !border-lime-400"
      />
    </div>
  );
});

CustomNodeComp.displayName = 'CustomNodeComp';
export default CustomNodeComp;
