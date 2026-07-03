import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { BarChart3 } from 'lucide-react';

const BATCH_LABELS = {
  split_newline: 'Split by Newline',
  split_comma: 'Split by Comma',
  json_array: 'JSON Array',
};

const BatchNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const hasJson = config.subworkflow_json && config.subworkflow_json.trim().length > 0;
  const mode = config.batch_mode || 'split_newline';

  return (
    <div className="min-w-[160px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <BarChart3 className="w-3 h-3 text-pink-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Batch</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-[10px] text-gray-400 truncate">
          {hasJson ? 'Configured' : 'No sub-workflow set'}
        </p>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-pink-900/40 text-pink-300 font-medium">
            {BATCH_LABELS[mode] || mode}
          </span>
        </div>
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

BatchNode.displayName = 'BatchNode';
export default BatchNode;
