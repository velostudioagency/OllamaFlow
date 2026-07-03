import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Send } from 'lucide-react';

const WebhookOutputNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const url = config.webhook_url || 'Not configured';
  const method = config.method || 'POST';
  const displayUrl = url.length > 30 ? url.substring(0, 30) + '...' : url;

  return (
    <div className={`min-w-[180px] rounded-lg border ${selected ? 'border-orange-400 shadow-lg shadow-orange-500/20' : 'border-[#333]'} bg-[#1a1a1a] overflow-hidden`}>
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <Send className="w-3 h-3 text-orange-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase">Webhook Output</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        <p className="text-xs text-gray-400">
          <span className="text-orange-300">{method}</span> {displayUrl}
        </p>
      </div>
      <Handle type="target" position={Position.Top} className="!bg-orange-500 !border-orange-400" />
    </div>
  );
});

export default WebhookOutputNode;
