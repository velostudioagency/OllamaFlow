import React from 'react';
import { Coins, Cpu, ArrowDown, ArrowUp, DollarSign } from 'lucide-react';

const PROVIDER_COLORS = {
  ollama: '#22C55E',
  groq: '#F59E0B',
  openai: '#10B981',
  anthropic: '#F97316',
};

const PROVIDER_LABELS = {
  ollama: 'Ollama',
  groq: 'Groq',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
};

export default function TokenUsagePanel({ tokenUsage }) {
  if (!tokenUsage || !tokenUsage.nodes || tokenUsage.nodes.length === 0) {
    return null;
  }

  const totalCost = tokenUsage.total_estimated_cost || 0;
  const totalTokens = tokenUsage.total_tokens || 0;
  const promptTokens = tokenUsage.total_prompt_tokens || 0;
  const completionTokens = tokenUsage.total_completion_tokens || 0;
  const duration = tokenUsage.duration_ms || 0;

  return (
    <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-3 space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <Coins className="w-4 h-4 text-yellow-400" />
        <span className="text-xs font-semibold text-gray-300 uppercase">Token Usage</span>
      </div>

      <div className="grid grid-cols-4 gap-2">
        <div className="bg-[#0f0f0f] rounded px-2 py-1.5">
          <p className="text-[10px] text-gray-500 uppercase">Total</p>
          <p className="text-sm font-bold text-white">{formatNumber(totalTokens)}</p>
        </div>
        <div className="bg-[#0f0f0f] rounded px-2 py-1.5">
          <p className="text-[10px] text-gray-500 uppercase flex items-center gap-0.5">
            <ArrowDown className="w-2.5 h-2.5" /> Input
          </p>
          <p className="text-sm font-bold text-blue-400">{formatNumber(promptTokens)}</p>
        </div>
        <div className="bg-[#0f0f0f] rounded px-2 py-1.5">
          <p className="text-[10px] text-gray-500 uppercase flex items-center gap-0.5">
            <ArrowUp className="w-2.5 h-2.5" /> Output
          </p>
          <p className="text-sm font-bold text-purple-400">{formatNumber(completionTokens)}</p>
        </div>
        <div className="bg-[#0f0f0f] rounded px-2 py-1.5">
          <p className="text-[10px] text-gray-500 uppercase flex items-center gap-0.5">
            <DollarSign className="w-2.5 h-2.5" /> Cost
          </p>
          <p className={`text-sm font-bold ${totalCost > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
            {totalCost > 0 ? `$${totalCost.toFixed(4)}` : 'Free'}
          </p>
        </div>
      </div>

      <div className="space-y-1.5">
        {tokenUsage.nodes.map((node, idx) => (
          <div key={idx} className="flex items-center gap-2 text-[11px]">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: PROVIDER_COLORS[node.provider] || '#666' }}
            />
            <span className="text-gray-400 truncate max-w-[120px]">{node.node_id}</span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-400">{PROVIDER_LABELS[node.provider] || node.provider}</span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-500 truncate max-w-[100px]">{node.model}</span>
            <span className="ml-auto text-gray-300">{formatNumber(node.total_tokens)}</span>
            {node.estimated_cost > 0 && (
              <span className="text-yellow-500">${node.estimated_cost.toFixed(4)}</span>
            )}
          </div>
        ))}
      </div>

      {duration > 0 && (
        <div className="text-[10px] text-gray-500 text-right">
          Completed in {(duration / 1000).toFixed(1)}s
        </div>
      )}
    </div>
  );
}

function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}
