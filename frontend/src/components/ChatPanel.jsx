import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Loader2, Clock, Copy, X, FileText, Square } from 'lucide-react';
import axios from 'axios';

export default function ChatPanel({ workflow }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const addMessage = (msg) => {
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), ...msg }]);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const cleanOutput = (text) => {
    if (!text) return text;
    return text
      .split('\n')
      .filter((line) => line.trim().length > 0)
      .join('\n');
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const stopResponse = () => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }));
      ws.close();
    }
    wsRef.current = null;
    setMessages((prev) =>
      prev.map((m) =>
        m.role === 'assistant' && m.status === 'running'
          ? { ...m, status: 'stopped', errors: ['Stopped by user'] }
          : m
      )
    );
    setIsSending(false);
  };

  const sendMessage = async () => {
    const text = inputText.trim();
    if (!text && !selectedFile) return;
    if (isSending) return;
    if (!workflow || !workflow.nodes || workflow.nodes.length === 0) {
      addMessage({
        role: 'system',
        content: 'No workflow loaded. Build a workflow on the canvas first.',
      });
      return;
    }

    setIsSending(true);
    setInputText('');

    const userMsg = {
      role: 'user',
      content: text || (selectedFile ? `Uploaded: ${selectedFile.name}` : ''),
    };
    addMessage(userMsg);

    let filePath = null;
    if (selectedFile) {
      try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        const uploadResp = await axios.post('/api/upload', formData);
        filePath = uploadResp.data.file_path;
      } catch (err) {
        addMessage({
          role: 'system',
          content: `File upload failed: ${err.message}`,
        });
        setIsSending(false);
        setSelectedFile(null);
        return;
      }
    }

    const responseMsg = {
      role: 'assistant',
      content: '',
      status: 'running',
      output: '',
      logs: [],
      errors: [],
      duration: null,
      streamText: '',
    };
    addMessage(responseMsg);

    try {
      const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/chat/run`);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({
          text: text,
          file_path: filePath,
          workflow: workflow,
        }));
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === 'stream') {
          const token = msg.data?.token || '';
          setMessages((prev) =>
            prev.map((m) => {
              if (m.role !== 'assistant' || m.status !== 'running') return m;
              return { ...m, streamText: (m.streamText || '') + token };
            })
          );
        } else if (msg.type === 'log') {
          const log = msg.data;
          setMessages((prev) =>
            prev.map((m) => {
              if (m.role !== 'assistant' || m.status !== 'running') return m;
              return { ...m, logs: [...(m.logs || []), log] };
            })
          );
        } else if (msg.type === 'complete') {
          const data = msg.data;
          setMessages((prev) =>
            prev.map((m) => {
              if (m.role !== 'assistant' || m.status !== 'running') return m;
              return {
                ...m,
                status: data.status === 'error' ? 'error' : 'completed',
                output: data.output || '',
                errors: data.errors || [],
                duration: data.duration,
                logs: data.logs || m.logs,
              };
            })
          );
          setIsSending(false);
          wsRef.current = null;
          ws.close();
        } else if (msg.type === 'error') {
          setMessages((prev) =>
            prev.map((m) => {
              if (m.role !== 'assistant' || m.status !== 'running') return m;
              return { ...m, status: 'error', errors: [msg.message] };
            })
          );
          setIsSending(false);
          wsRef.current = null;
          ws.close();
        }
      };

      ws.onerror = () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.role === 'assistant' && m.status === 'running'
              ? { ...m, status: 'error', errors: ['WebSocket connection failed. Is the backend running?'] }
              : m
          )
        );
        setIsSending(false);
        wsRef.current = null;
      };

      ws.onclose = () => {
        wsRef.current = null;
        setIsSending(false);
      };

      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.role === 'assistant' && m.status === 'running'
            ? { ...m, status: 'error', errors: [`Failed to start workflow: ${err.message}`] }
            : m
        )
      );
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-[#0f0f0f] overflow-hidden">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-4xl mb-4">💬</div>
            <h2 className="text-lg font-semibold text-gray-300 mb-2">Chat with your workflow</h2>
            <p className="text-sm text-gray-500 max-w-md">
              Send a message or upload a file to trigger the currently loaded workflow.
              Results stream in real-time via WebSocket.
            </p>
          </div>
        )}

        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'user' ? (
                <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm">
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              ) : msg.role === 'system' ? (
                <div className="max-w-[85%] bg-yellow-900/30 border border-yellow-700/50 text-yellow-300 rounded-lg px-4 py-3 text-sm">
                  {msg.content}
                </div>
              ) : (
                <div className="max-w-[85%] bg-[#1a1a1a] border border-[#333] rounded-2xl rounded-bl-sm px-4 py-3">
                  {msg.status === 'running' && !msg.output && !msg.streamText && (
                    <div className="flex items-center gap-2 text-gray-400 text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Running workflow...</span>
                      <button
                        onClick={stopResponse}
                        className="flex items-center gap-1 ml-2 px-2 py-0.5 text-[10px] font-medium bg-red-600 hover:bg-red-700 text-white rounded transition"
                      >
                        <Square className="w-2.5 h-2.5" />
                        Stop
                      </button>
                    </div>
                  )}

                  {msg.streamText && (
                    <div className="mb-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-yellow-400 text-[10px] uppercase tracking-wide font-semibold">
                          AI Response
                        </span>
                        {msg.status === 'running' && (
                          <Loader2 className="w-3 h-3 text-yellow-400 animate-spin" />
                        )}
                      </div>
                      <div className="text-gray-200 whitespace-pre-wrap break-words text-xs leading-relaxed font-mono">
                        {cleanOutput(msg.streamText)}
                        {msg.status === 'running' && (
                          <span className="animate-pulse text-yellow-400">|</span>
                        )}
                      </div>
                    </div>
                  )}

                  {msg.output && msg.status !== 'running' && (
                    <div className="mb-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] uppercase tracking-wide font-semibold text-green-400">
                          Result
                        </span>
                        <div className="flex items-center gap-2">
                          {msg.duration && (
                            <span className="text-[10px] text-gray-500 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {msg.duration}s
                            </span>
                          )}
                          <button
                            onClick={() => copyToClipboard(msg.output)}
                            className="p-1 text-gray-500 hover:text-white transition"
                            title="Copy"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <div className="text-gray-300 whitespace-pre-wrap break-words text-xs leading-relaxed font-mono max-h-96 overflow-y-auto">
                        {cleanOutput(msg.output)}
                      </div>
                    </div>
                  )}

                  {msg.errors && msg.errors.length > 0 && msg.status !== 'running' && (
                    <div className="mt-2">
                      {msg.errors.map((err, i) => (
                        <div key={i} className={`text-xs ${msg.status === 'stopped' ? 'text-yellow-400' : 'text-red-400'}`}>
                          {err}
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.status === 'running' && (msg.streamText || msg.output) && (
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex items-center gap-1.5 text-gray-500 text-[10px]">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Still processing...
                      </div>
                      <button
                        onClick={stopResponse}
                        className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium bg-red-600 hover:bg-red-700 text-white rounded transition"
                      >
                        <Square className="w-2.5 h-2.5" />
                        Stop
                      </button>
                    </div>
                  )}

                  {msg.status === 'error' && !msg.output && (
                    <div className="text-red-400 text-sm">
                      Workflow failed. Check the errors above.
                    </div>
                  )}

                  {msg.status === 'stopped' && !msg.output && (
                    <div className="text-yellow-400 text-sm">
                      Workflow stopped by user.
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-[#333] bg-[#141414] px-4 py-3">
        <div className="max-w-3xl mx-auto">
          {selectedFile && (
            <div className="mb-2 flex items-center gap-2 bg-[#1a1a1a] border border-[#333] rounded-lg px-3 py-2 text-sm text-gray-300">
              <FileText className="w-4 h-4 text-blue-400" />
              <span className="flex-1 truncate">{selectedFile.name}</span>
              <span className="text-xs text-gray-500">
                {(selectedFile.size / 1024).toFixed(1)}KB
              </span>
              <button onClick={removeFile} className="p-1 text-gray-500 hover:text-white transition">
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          <div className="flex items-end gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 text-gray-400 hover:text-white hover:bg-[#333] rounded-lg transition shrink-0"
              title="Upload file"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileSelect}
            />

            <div className="flex-1 relative">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message or upload a file..."
                rows={1}
                className="w-full bg-[#0f0f0f] border border-[#333] rounded-xl px-4 py-3 text-sm text-white resize-none focus:outline-none focus:border-blue-500 placeholder-gray-600"
                style={{ minHeight: '44px', maxHeight: '120px' }}
              />
            </div>

            <button
              onClick={sendMessage}
              disabled={isSending || (!inputText.trim() && !selectedFile)}
              className={`p-2.5 rounded-lg transition shrink-0 ${
                isSending || (!inputText.trim() && !selectedFile)
                  ? 'bg-[#333] text-gray-600 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isSending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
