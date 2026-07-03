import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { GitBranch } from 'lucide-react';

const SwitchNode = memo(({ data, selected }) => {
  const config = data.config || {};
  const cases = config.cases || '';
  const caseLines = cases.split('\n').filter(l => l.includes(':'));

  return (
    <div className="min-w-[200px]">
      <div className="bg-[#1a1a1a] rounded-t-lg px-3 py-1.5 border-b border-[#333] flex items-center gap-2">
        <GitBranch className="w-3 h-3 text-amber-400" />
        <span className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide">Switch</span>
      </div>
      <div className="bg-[#1a1a1a] px-3 py-2 rounded-b-lg">
        {caseLines.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {caseLines.map((line, i) => {
              const label = line.split(':').slice(1).join(':').trim() || line.split(':')[0].trim();
              return (
                <span key={i} className="text-[9px] bg-amber-900/30 text-amber-300 px-1.5 py-0.5 rounded">
                  {label}
                </span>
              );
            })}
            <span className="text-[9px] bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded">
              {config.default_case || 'default'}
            </span>
          </div>
        ) : (
          <p className="text-[10px] text-gray-500">No cases defined</p>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-amber-500 !border-amber-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-0"
        style={{ left: '15%' }}
        className="!bg-amber-500 !border-amber-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-1"
        style={{ left: '40%' }}
        className="!bg-amber-500 !border-amber-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-2"
        style={{ left: '65%' }}
        className="!bg-amber-500 !border-amber-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="handle-default"
        style={{ left: '90%' }}
        className="!bg-gray-500 !border-gray-400"
      />
    </div>
  );
});

SwitchNode.displayName = 'SwitchNode';
export default SwitchNode;
