import React, { useState, useEffect } from 'react';
import { X, Clock, CheckCircle, AlertCircle, Trash2, Download } from 'lucide-react';
import axios from 'axios';

export default function ExecutionHistory({ onClose }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const resp = await axios.get('/api/history');
      setHistory(resp.data.history || []);
    } catch (err) {
      console.error('Failed to fetch history');
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    if (!confirm('Clear all execution history?')) return;
    try {
      await axios.delete('/api/history');
      setHistory([]);
      setSelectedRun(null);
    } catch (err) {
      alert('Failed to clear history');
    }
  };

  const exportLogs = async (format = 'json') => {
    try {
      const resp = await axios.get(`/api/logs/export?format=${format}`, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `logs.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export logs');
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '—';
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}m ${s}s`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-[#1a1a1a] border border-[#333] rounded-xl w-[800px] max-h-[80vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-5 py-3 border-b border-[#333]">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-white">Execution History</h2>
            <span className="text-xs text-gray-500">({history.length} runs)</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => exportLogs('json')} className="p-1.5 text-gray-400 hover:text-white hover:bg-[#333] rounded transition" title="Export JSON">
              <Download className="w-3.5 h-3.5" />
            </button>
            <button onClick={clearHistory} className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-[#333] rounded transition" title="Clear History">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-white hover:bg-[#333] rounded transition">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <div className="flex flex-1 overflow-hidden">
          <div className="w-1/2 overflow-y-auto border-r border-[#333]">
            {loading ? (
              <div className="p-4 text-xs text-gray-500">Loading...</div>
            ) : history.length === 0 ? (
              <div className="p-4 text-xs text-gray-500">No execution history yet. Run a workflow to see it here.</div>
            ) : (
              history.map((run) => (
                <button
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  className={`w-full text-left px-4 py-3 border-b border-[#222] hover:bg-[#222] transition ${
                    selectedRun?.id === run.id ? 'bg-[#222]' : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-white truncate">{run.workflow_name}</span>
                    {run.status === 'completed' ? (
                      <CheckCircle className="w-3 h-3 text-green-400 shrink-0" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-yellow-400 shrink-0" />
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-gray-500">
                    <span>{run.started_at?.split('T')[1]?.split('.')[0] || '—'}</span>
                    <span>{formatDuration(run.duration_seconds)}</span>
                    <span>{run.node_count} nodes</span>
                    {run.error_count > 0 && (
                      <span className="text-red-400">{run.error_count} errors</span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
          <div className="w-1/2 overflow-y-auto p-4">
            {selectedRun ? (
              <div>
                <h3 className="text-xs font-semibold text-white mb-2">{selectedRun.workflow_name}</h3>
                <div className="space-y-1 text-[10px] text-gray-400 mb-3">
                  <p>ID: <span className="text-gray-300 font-mono">{selectedRun.id}</span></p>
                  <p>Started: <span className="text-gray-300">{selectedRun.started_at}</span></p>
                  <p>Duration: <span className="text-gray-300">{formatDuration(selectedRun.duration_seconds)}</span></p>
                  <p>Status: <span className={selectedRun.status === 'completed' ? 'text-green-400' : 'text-yellow-400'}>{selectedRun.status}</span></p>
                </div>
                {selectedRun.output_preview && (
                  <div className="mb-3">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Output Preview</p>
                    <pre className="text-[10px] text-gray-300 bg-[#0f0f0f] rounded p-2 max-h-32 overflow-y-auto whitespace-pre-wrap">
                      {selectedRun.output_preview}
                    </pre>
                  </div>
                )}
                <div>
                  <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Logs ({selectedRun.logs?.length || 0})</p>
                  <div className="space-y-0.5 max-h-60 overflow-y-auto">
                    {selectedRun.logs?.map((log, i) => (
                      <div key={i} className="flex gap-1.5 text-[10px] font-mono">
                        <span className="text-gray-600 shrink-0">{log.timestamp}</span>
                        <span className={`shrink-0 ${
                          log.status === 'error' ? 'text-red-400' :
                          log.status === 'success' ? 'text-green-400' :
                          log.status === 'running' ? 'text-yellow-400' : 'text-gray-400'
                        }`}>
                          {log.status === 'error' ? '✗' : log.status === 'success' ? '✓' : log.status === 'running' ? '►' : '•'}
                        </span>
                        <span className="text-gray-300 truncate">{log.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-600 text-center mt-8">Select a run to view details</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
