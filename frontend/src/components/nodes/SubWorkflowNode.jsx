import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Layers } from 'lucide-react';

const SubWorkflowNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const hasJson = config.subworkflow_json && config.subworkflow_json.trim().length > 0;
  const passInput = config.pass_input !== false;

  return (
    <div className="min-w-[160px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Layers className="w-3 h-3 text-sky-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Sub-Workflow</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-[10px] text-gray-400 truncate">
          {hasJson ? 'Configured' : 'No sub-workflow set'}
        </p>
        <div className="flex items-center gap-1.5 mt-1">
          <span className={`text-[9px] px-1.5 py-0.5 rounded ${passInput ? 'bg-sky-900/40 text-sky-300' : 'bg-gray-800 text-gray-400'} font-medium`}>
            {passInput ? 'Pass Input' : 'No Input'}
          </span>
        </div>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-sky-500 !border-sky-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-sky-500 !border-sky-400"
      />
    </div>
  );
});

SubWorkflowNode.displayName = 'SubWorkflowNode';
export default SubWorkflowNode;
