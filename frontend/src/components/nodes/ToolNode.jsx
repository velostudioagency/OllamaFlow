import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Wrench } from 'lucide-react';

const TOOL_ICONS = {
  web_search: '🔍',
  read_file: '📖',
  write_file: '✏️',
  run_code: '💻',
  send_email: '📧',
  http_request: '🌐',
  calculate: '🧮',
  get_datetime: '🕐',
};

const ToolNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const toolName = config.tool_name || 'web_search';

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-orange-500" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Tool</span>
        <Wrench className="w-3 h-3 text-orange-400 ml-auto" />
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-white flex items-center gap-1.5">
          <span>{TOOL_ICONS[toolName] || '🔧'}</span>
          {toolName}
        </p>
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-orange-500 !border-orange-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-orange-500 !border-orange-400"
      />
    </div>
  );
});

ToolNode.displayName = 'ToolNode';
export default ToolNode;
