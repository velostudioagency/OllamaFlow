import React, { useState, useEffect, useRef } from 'react';
import { X, Trash2, Upload, Clock } from 'lucide-react';
import axios from 'axios';

export default function ConfigPanel({ node, onUpdateConfig, onUpdateLabel, onDelete, onClose }) {
  const [models, setModels] = useState([]);
  const [toolsList, setToolsList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchModels();
    fetchTools();
  }, []);

  const fetchModels = async () => {
    try {
      const resp = await axios.get('/api/models');
      setModels(resp.data.models || []);
    } catch (err) {
      setModels([]);
    }
  };

  const fetchTools = async () => {
    try {
      const resp = await axios.get('/api/tools');
      setToolsList(Object.keys(resp.data.details || {}));
    } catch (err) {
      setToolsList([]);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const resp = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      onUpdateConfig(node.id, { file_path: resp.data.file_path });
    } catch (err) {
      setUploadError('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  if (!node) return null;

  const config = node.data.config || {};
  const type = node.type;

  const renderField = (key, schema) => {
    const value = config[key] !== undefined ? config[key] : schema.default;

    if (schema.type === 'string') {
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs text-gray-400 mb-1">{schema.label}</label>
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onUpdateConfig(node.id, { [key]: e.target.value })}
            className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>
      );
    }

    if (schema.type === 'textarea') {
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs text-gray-400 mb-1">{schema.label}</label>
          <textarea
            value={value || ''}
            onChange={(e) => onUpdateConfig(node.id, { [key]: e.target.value })}
            rows={4}
            className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>
      );
    }

    if (schema.type === 'select') {
      const options = key === 'model' && models.length > 0
        ? models
        : key === 'tool_name' && toolsList.length > 0
        ? toolsList
        : schema.options || [];
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs text-gray-400 mb-1">{schema.label}</label>
          <select
            value={value || ''}
            onChange={(e) => {
              const newConfig = { [key]: e.target.value };
              if (key === 'tool_name') {
                newConfig.params = {};
              }
              onUpdateConfig(node.id, newConfig);
            }}
            className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            {options.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>
      );
    }

    if (schema.type === 'multiselect') {
      const options = key === 'tools' && toolsList.length > 0 ? toolsList : (schema.options || []);
      const selected = Array.isArray(value) ? value : [];
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs text-gray-400 mb-1">{schema.label}</label>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {options.map((opt) => (
              <label key={opt} className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer hover:text-white">
                <input
                  type="checkbox"
                  checked={selected.includes(opt)}
                  onChange={(e) => {
                    const newVal = e.target.checked
                      ? [...selected, opt]
                      : selected.filter((s) => s !== opt);
                    onUpdateConfig(node.id, { [key]: newVal });
                  }}
                  className="rounded"
                />
                {opt}
              </label>
            ))}
          </div>
        </div>
      );
    }

    if (schema.type === 'slider') {
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs text-gray-400 mb-1">
            {schema.label}: <span className="text-white">{value}</span>
          </label>
          <input
            type="range"
            min={schema.min}
            max={schema.max}
            step={schema.step}
            value={value || schema.default}
            onChange={(e) => onUpdateConfig(node.id, { [key]: parseFloat(e.target.value) })}
            className="w-full accent-blue-500"
          />
        </div>
      );
    }

    if (schema.type === 'number') {
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs text-gray-400 mb-1">{schema.label}</label>
          <input
            type="number"
            value={value || 0}
            onChange={(e) => onUpdateConfig(node.id, { [key]: parseInt(e.target.value) || 0 })}
            className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>
      );
    }

    if (schema.type === 'boolean') {
      return (
        <div key={key} className="mb-3 flex items-center justify-between">
          <label className="text-xs text-gray-400">{schema.label}</label>
          <button
            onClick={() => onUpdateConfig(node.id, { [key]: !value })}
            className={`w-10 h-5 rounded-full transition-colors relative ${value ? 'bg-blue-600' : 'bg-[#333]'}`}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                value ? 'translate-x-5' : 'translate-x-0.5'
              }`}
            />
          </button>
        </div>
      );
    }

    return null;
  };

  const nodeConfigs = {
    input: {
      prompt: { type: 'string', label: 'Goal / Prompt' },
      input_type: { type: 'select', label: 'Input Type', options: ['text', 'file_upload', 'scheduled'] },
    },
    llm: {
      model: { type: 'select', label: 'Model' },
      system_prompt: { type: 'textarea', label: 'System Prompt' },
      temperature: { type: 'slider', label: 'Temperature', min: 0, max: 1, step: 0.1 },
      max_tokens: { type: 'slider', label: 'Max Tokens', min: 100, max: 4000, step: 100 },
    },
    tool: {
      tool_name: { type: 'select', label: 'Tool' },
    },
    memory: {
      namespace: { type: 'string', label: 'Namespace' },
      memory_type: { type: 'select', label: 'Memory Type', options: ['short_term', 'long_term'] },
      action: { type: 'select', label: 'Action', options: ['remember', 'recall', 'search', 'clear'] },
      search_query: { type: 'string', label: 'Search Query' },
    },
    condition: {
      condition: { type: 'string', label: 'Condition' },
    },
    loop: {
      max_iterations: { type: 'number', label: 'Max Iterations' },
      stop_condition: { type: 'string', label: 'Stop Condition' },
    },
    agent: {
      model: { type: 'select', label: 'Model' },
      tools: { type: 'multiselect', label: 'Tools' },
      system_prompt: { type: 'textarea', label: 'Agent Persona' },
      max_steps: { type: 'slider', label: 'Max Steps', min: 1, max: 20, step: 1 },
      memory: { type: 'boolean', label: 'Enable Memory' },
    },
    output: {},
  };

  const fields = nodeConfigs[type] || {};
  const fieldEntries = Object.entries(fields);

  const typeColors = {
    input: '#3B82F6',
    llm: '#8B5CF6',
    tool: '#F97316',
    memory: '#22C55E',
    condition: '#EAB308',
    loop: '#EC4899',
    agent: '#EF4444',
    output: '#6B7280',
  };

  const TOOL_PARAMS = {
    web_search: [
      { name: 'query', label: 'Search Query', type: 'string', required: true },
      { name: 'num_results', label: 'Num Results', type: 'number', default: 5 },
    ],
    read_file: [
      { name: 'file_path', label: 'File Path', type: 'string', required: true },
    ],
    write_file: [
      { name: 'file_path', label: 'File Path', type: 'string', required: true },
      { name: 'content', label: 'Content', type: 'textarea', required: true },
    ],
    run_code: [
      { name: 'code', label: 'Python Code', type: 'textarea', required: true },
    ],
    send_email: [
      { name: 'to', label: 'To Email', type: 'string', required: true },
      { name: 'subject', label: 'Subject', type: 'string', required: true },
      { name: 'body', label: 'Body', type: 'textarea', required: true },
      { name: 'smtp_server', label: 'SMTP Server', type: 'string', default: 'smtp.gmail.com' },
      { name: 'smtp_port', label: 'SMTP Port', type: 'number', default: 587 },
      { name: 'username', label: 'Username (Email)', type: 'string' },
      { name: 'password', label: 'Password (App Password)', type: 'string' },
    ],
    http_request: [
      { name: 'url', label: 'URL', type: 'string', required: true },
      { name: 'method', label: 'Method', type: 'select', options: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], default: 'GET' },
      { name: 'headers', label: 'Headers (JSON)', type: 'textarea' },
      { name: 'body', label: 'Body', type: 'textarea' },
      { name: 'timeout', label: 'Timeout (s)', type: 'number', default: 30 },
    ],
    calculate: [
      { name: 'expression', label: 'Expression', type: 'string', required: true },
    ],
    get_datetime: [
      { name: 'format_str', label: 'Format', type: 'string', default: '%Y-%m-%d %H:%M:%S' },
    ],
    run_command: [
      { name: 'command', label: 'Command', type: 'string', required: true },
      { name: 'working_directory', label: 'Working Directory', type: 'string' },
      { name: 'timeout', label: 'Timeout (s)', type: 'number', default: 60 },
    ],
  };

  const renderToolParams = (toolName, params, nodeId) => {
    const toolParamDefs = TOOL_PARAMS[toolName] || [];
    return toolParamDefs.map((p) => {
      const value = params[p.name] !== undefined ? params[p.name] : (p.default || '');
      const updateParam = (val) => {
        const newParams = { ...params, [p.name]: val };
        onUpdateConfig(nodeId, { params: newParams });
      };

      if (p.type === 'string') {
        return (
          <div key={p.name} className="mb-2">
            <label className="block text-xs text-gray-400 mb-1">
              {p.label} {p.required && <span className="text-red-400">*</span>}
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => updateParam(e.target.value)}
              className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        );
      }

      if (p.type === 'textarea') {
        return (
          <div key={p.name} className="mb-2">
            <label className="block text-xs text-gray-400 mb-1">
              {p.label} {p.required && <span className="text-red-400">*</span>}
            </label>
            <textarea
              value={value}
              onChange={(e) => updateParam(e.target.value)}
              rows={3}
              className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>
        );
      }

      if (p.type === 'number') {
        return (
          <div key={p.name} className="mb-2">
            <label className="block text-xs text-gray-400 mb-1">{p.label}</label>
            <input
              type="number"
              value={value}
              onChange={(e) => updateParam(parseInt(e.target.value) || 0)}
              className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        );
      }

      if (p.type === 'select') {
        return (
          <div key={p.name} className="mb-2">
            <label className="block text-xs text-gray-400 mb-1">{p.label}</label>
            <select
              value={value}
              onChange={(e) => updateParam(e.target.value)}
              className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              {(p.options || []).map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
        );
      }

      return null;
    });
  };

  return (
    <div className="w-72 bg-[#141414] border-l border-[#333] flex flex-col shrink-0 overflow-hidden">
      <div className="px-4 py-3 border-b border-[#333] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: typeColors[type] }} />
          <span className="text-xs font-semibold text-white uppercase">{type} Node</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onDelete(node.id)}
            className="p-1 text-gray-500 hover:text-red-500 transition"
            title="Delete Node"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onClose}
            className="p-1 text-gray-500 hover:text-white transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3">
        <div className="mb-3">
          <label className="block text-xs text-gray-400 mb-1">Node Label</label>
          <input
            type="text"
            value={node.data.label || ''}
            onChange={(e) => onUpdateLabel(node.id, e.target.value)}
            className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="w-full h-px bg-[#333] my-3" />

        {fieldEntries.map(([key, schema]) => renderField(key, schema))}

        {type === 'input' && config.input_type === 'file_upload' && (
          <div className="mt-2">
            <div className="w-full h-px bg-[#333] my-3" />
            <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2">Upload File</p>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileUpload}
              className="hidden"
              accept=".txt,.md,.py,.json,.csv,.pdf,.docx,.xlsx"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full flex items-center justify-center gap-2 bg-[#1a1a2e] border border-[#333] rounded px-3 py-2 text-xs text-white hover:border-blue-500 transition disabled:opacity-50"
            >
              <Upload className="w-3.5 h-3.5" />
              {uploading ? 'Uploading...' : 'Choose File'}
            </button>
            {config.file_path && (
              <p className="text-[10px] text-green-400 mt-1 truncate">{config.file_path.split(/[/\\]/).pop()}</p>
            )}
            {uploadError && <p className="text-[10px] text-red-400 mt-1">{uploadError}</p>}
          </div>
        )}

        {type === 'input' && config.input_type === 'scheduled' && (
          <div className="mt-2">
            <div className="w-full h-px bg-[#333] my-3" />
            <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2">Schedule Config</p>
            <div className="mb-3">
              <label className="block text-xs text-gray-400 mb-1">Run Every (minutes)</label>
              <input
                type="number"
                value={config.interval_minutes || 60}
                onChange={(e) => onUpdateConfig(node.id, { interval_minutes: parseInt(e.target.value) || 60 })}
                min="1"
                className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="mb-3 flex items-center justify-between">
              <label className="text-xs text-gray-400">Enabled</label>
              <button
                onClick={() => onUpdateConfig(node.id, { schedule_enabled: !(config.schedule_enabled !== false) })}
                className={`w-10 h-5 rounded-full transition-colors relative ${config.schedule_enabled !== false ? 'bg-blue-600' : 'bg-[#333]'}`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                    config.schedule_enabled !== false ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
            <p className="text-[10px] text-gray-500 mt-2">
              <Clock className="w-3 h-3 inline mr-1" />
              Workflow runs automatically every {config.interval_minutes || 60} min
            </p>
          </div>
        )}

        {type === 'tool' && config.tool_name && (
          <div className="mt-2">
            <div className="w-full h-px bg-[#333] my-3" />
            <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2">Tool Parameters</p>
            {renderToolParams(config.tool_name, config.params || {}, node.id)}
          </div>
        )}

        {fieldEntries.length === 0 && type !== 'tool' && (
          <p className="text-xs text-gray-600 text-center mt-8">No configurable options</p>
        )}
      </div>
    </div>
  );
}
