import React, { useState, useRef, useEffect } from 'react';
import { X, Copy, Download, ChevronUp, ChevronDown, Loader2, Coins } from 'lucide-react';
import TokenUsagePanel from './TokenUsagePanel';

export default function OutputPanel({ logs, finalOutput, errors, runDuration, streamText, streamingNode, isRunning, onClose, tokenUsage }) {
  const [activeTab, setActiveTab] = useState('logs');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const logsRef = useRef(null);

  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, [logs, streamText]);

  useEffect(() => {
    if (finalOutput && !isRunning) {
      setActiveTab('output');
    }
  }, [finalOutput, isRunning]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(finalOutput).then(() => {
      alert('Copied to clipboard!');
    });
  };

  const downloadAsTxt = () => {
    const blob = new Blob([finalOutput], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'output.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadAsPdf = async () => {
    try {
      const resp = await fetch('/api/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: finalOutput }),
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'output.pdf';
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert('PDF generation not available on backend. Use TXT download.');
      }
    } catch {
      alert('PDF generation not available. Use TXT download.');
    }
  };

  const formatTime = (ts) => {
    return ts || '';
  };

  const statusIcons = {
    info: 'ℹ️',
    running: '⚡',
    success: '✅',
    error: '❌',
    warning: '⚠️',
  };

  return (
    <div
      className={`bg-[#141414] border-t border-[#333] flex flex-col shrink-0 transition-all ${
        isCollapsed ? 'h-10' : 'h-80'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#333] shrink-0">
        <div className="flex items-center gap-1">
          {['logs', 'output', 'errors', 'tokens'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 text-xs rounded transition ${
                activeTab === tab
                  ? 'bg-[#333] text-white'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab === 'logs' && 'Live Logs'}
              {tab === 'output' && 'Final Output'}
              {tab === 'errors' && `Errors${errors.length ? ` (${errors.length})` : ''}`}
              {tab === 'tokens' && <span className="flex items-center gap-1"><Coins className="w-3 h-3" /> Tokens</span>}
            </button>
          ))}
        </div>
        {runDuration && (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-[#1a1a1a] rounded text-xs">
            <span className="text-gray-500">Completed in</span>
            <span className="text-green-400 font-mono font-medium">{runDuration}s</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          {activeTab === 'output' && finalOutput && (
            <>
              <button
                onClick={copyToClipboard}
                className="p-1 text-gray-500 hover:text-white transition"
                title="Copy to Clipboard"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={downloadAsTxt}
                className="p-1 text-gray-500 hover:text-white transition"
                title="Download as TXT"
              >
                <Download className="w-3.5 h-3.5" />
              </button>
            </>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 text-gray-500 hover:text-white transition"
          >
            {isCollapsed ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onClose}
            className="p-1 text-gray-500 hover:text-white transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div ref={logsRef} className="flex-1 overflow-y-auto px-4 py-2 font-mono text-xs">
          {activeTab === 'logs' && (
            <div className="space-y-1">
              {logs.length === 0 && !streamText && (
                <p className="text-gray-600">No logs yet. Run the workflow to see output.</p>
              )}
              {logs.map((log, i) => (
                <div key={i} className="flex gap-2 items-start">
                  <span className="text-gray-600 shrink-0">[{log.timestamp}]</span>
                  <span className="shrink-0">{statusIcons[log.status] || '•'}</span>
                  <span className={`${
                    log.status === 'error' ? 'text-red-400' :
                    log.status === 'success' ? 'text-green-400' :
                    log.status === 'running' ? 'text-yellow-400' :
                    'text-gray-300'
                  }`}>
                    {log.message}
                  </span>
                </div>
              ))}
              {streamText && (
                <div className="mt-2 p-3 bg-[#1a1a2e] rounded border border-[#444]">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-yellow-400 text-[10px] uppercase tracking-wide font-semibold">AI Response</span>
                    {streamingNode && (
                      <span className="text-[10px] text-gray-500">from {streamingNode}</span>
                    )}
                    {isRunning && (
                      <Loader2 className="w-3 h-3 text-yellow-400 animate-spin" />
                    )}
                  </div>
                  <pre className="text-gray-200 whitespace-pre-wrap text-[11px] leading-relaxed">{streamText}<span className="animate-pulse text-yellow-400">|</span></pre>
                </div>
              )}
            </div>
          )}

          {activeTab === 'output' && (
            <div>
              {finalOutput ? (
                <pre className="text-gray-300 whitespace-pre-wrap">{finalOutput}</pre>
              ) : (
                <p className="text-gray-600">No output yet. Run the workflow to see results.</p>
              )}
            </div>
          )}

          {activeTab === 'errors' && (
            <div className="space-y-1">
              {errors.length === 0 && (
                <p className="text-gray-600">No errors.</p>
              )}
              {errors.map((err, i) => (
                <div key={i} className="text-red-400">
                  <span className="text-red-500">Error {i + 1}:</span> {err}
                </div>
              ))}
            </div>
          )}

          {activeTab === 'tokens' && (
            <div>
              {tokenUsage ? (
                <TokenUsagePanel tokenUsage={tokenUsage} />
              ) : (
                <p className="text-gray-600">No token usage data. Run the workflow to see usage.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
