import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Anchor } from 'lucide-react';

const WebhookNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const method = config.method || 'POST';
  const url = config.webhook_url || '';

  return (
    <div className="min-w-[180px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Anchor className="w-3 h-3 text-emerald-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Webhook</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400">Method: <span className="text-white">{method}</span></p>
        {url && (
          <p className="text-[10px] text-gray-500 truncate max-w-[160px]" title={url}>
            {url}
          </p>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-emerald-500 !border-emerald-400"
      />
    </div>
  );
});

WebhookNode.displayName = 'WebhookNode';
export default WebhookNode;
