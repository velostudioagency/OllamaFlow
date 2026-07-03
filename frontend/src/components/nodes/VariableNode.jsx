import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Package } from 'lucide-react';

const MODE_LABELS = {
  set: 'Set',
  get: 'Get',
  increment: '++',
  append: '+=',
};

const VariableNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const varName = config.variable_name || 'my_var';
  const mode = config.mode || 'set';
  const varType = config.variable_type || 'string';
  const value = config.variable_value || '';

  return (
    <div className="min-w-[160px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Package className="w-3 h-3 text-fuchsia-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Variable</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-white font-mono truncate">{varName}</p>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-fuchsia-900/40 text-fuchsia-300 font-medium">
            {MODE_LABELS[mode] || mode}
          </span>
          <span className="text-[9px] text-gray-500">{varType}</span>
        </div>
        {mode === 'set' && value && (
          <p className="text-[10px] text-gray-500 mt-1 truncate font-mono">{value}</p>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-fuchsia-500 !border-fuchsia-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-fuchsia-500 !border-fuchsia-400"
      />
    </div>
  );
});

VariableNode.displayName = 'VariableNode';
export default VariableNode;
