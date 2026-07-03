import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Shield } from 'lucide-react';

const GuardrailsNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const validationType = config.validation_type || 'not_empty';

  return (
    <div className="min-w-[200px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Shield className="w-3 h-3 text-rose-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Guardrails</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400">Check: <span className="text-white">{validationType}</span></p>
        {config.retry_on_fail && (
          <p className="text-[10px] text-amber-400">Retry: {config.max_retries || 3}x</p>
        )}
        <div className="flex justify-between mt-1.5 px-2">
          <span className="text-[9px] text-green-400 font-medium">Valid</span>
          <span className="text-[9px] text-red-400 font-medium">Invalid</span>
        </div>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-rose-500 !border-rose-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-valid"
        style={{ left: '30%' }}
        className="!bg-green-500 !border-green-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-invalid"
        style={{ left: '70%' }}
        className="!bg-red-500 !border-red-400"
      />
    </div>
  );
});

GuardrailsNode.displayName = 'GuardrailsNode';
export default GuardrailsNode;
