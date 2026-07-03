import React, { useState, useEffect, useRef } from 'react';
import { X, Trash2, Upload, Clock, Download, Brain, Wrench, Database, GitBranch, Repeat, FileOutput, Wand2, Link, Timer, Anchor, Shield, Package, Layers, BarChart3, Settings } from 'lucide-react';
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
      provider: { type: 'select', label: 'Provider', options: ['ollama', 'groq', 'openai', 'anthropic'] },
      model: { type: 'select', label: 'Model' },
      groq_model: { type: 'select', label: 'Groq Model',
        options: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'gemma2-9b-it', 'mixtral-8x7b-32768', 'meta-llama/llama-4-scout-17b-16e-instruct'] },
      openai_model: { type: 'select', label: 'OpenAI Model',
        options: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o1', 'o1-mini'] },
      anthropic_model: { type: 'select', label: 'Anthropic Model',
        options: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'] },
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
    output: {},
    transform: {
      transform_type: { type: 'select', label: 'Transform', options: ['regex_extract', 'regex_replace', 'substring', 'uppercase', 'lowercase', 'trim', 'replace', 'json_path', 'template'] },
      pattern: { type: 'string', label: 'Pattern / Path' },
      replacement: { type: 'string', label: 'Replacement' },
      template: { type: 'textarea', label: 'Template (use {{input}})' },
    },
    merge: {
      merge_mode: { type: 'select', label: 'Mode', options: ['concat', 'newline', 'json_merge', 'first', 'non_empty'] },
      separator: { type: 'string', label: 'Separator' },
    },
    delay: {
      delay_seconds: { type: 'number', label: 'Delay (seconds)' },
    },
    switch: {
      switch_field: { type: 'string', label: 'Context Key (blank = use input)' },
      cases: { type: 'textarea', label: 'Cases (one per line: value: label)' },
      default_case: { type: 'string', label: 'Default Label' },
    },
    webhook: {
      webhook_url: { type: 'string', label: 'Webhook URL' },
      method: { type: 'select', label: 'Method', options: ['POST', 'GET', 'PUT'] },
      auth_token: { type: 'string', label: 'Auth Token (optional)' },
    },
    guardrails: {
      validation_type: { type: 'select', label: 'Validation', options: ['not_empty', 'json_valid', 'contains', 'regex', 'max_length', 'min_length', 'custom'] },
      pattern: { type: 'string', label: 'Pattern / Required Text' },
      max_length: { type: 'number', label: 'Max/Min Length' },
      retry_on_fail: { type: 'boolean', label: 'Retry on Fail' },
      max_retries: { type: 'number', label: 'Max Retries' },
    },
    variable: {
      variable_name: { type: 'string', label: 'Variable Name' },
      variable_value: { type: 'textarea', label: 'Value / Expression' },
      variable_type: { type: 'select', label: 'Type', options: ['string', 'number', 'boolean', 'json'] },
      mode: { type: 'select', label: 'Mode', options: ['set', 'get', 'increment', 'append'] },
      default_value: { type: 'string', label: 'Default Value (for get)' },
    },
    subworkflow: {
      subworkflow_json: { type: 'textarea', label: 'Sub-Workflow JSON' },
      pass_input: { type: 'boolean', label: 'Pass Current Input' },
    },
    batch: {
      subworkflow_json: { type: 'textarea', label: 'Sub-Workflow JSON' },
      batch_mode: { type: 'select', label: 'Split Mode', options: ['split_newline', 'split_comma', 'json_array'] },
    },
    custom: {
      custom_code: { type: 'textarea', label: 'Python Code' },
      handler_name: { type: 'string', label: 'Handler Function' },
    },
    webhook_output: {
      webhook_url: { type: 'string', label: 'Webhook URL' },
      method: { type: 'select', label: 'Method', options: ['POST', 'PUT', 'PATCH'] },
      auth_token: { type: 'string', label: 'Auth Token' },
      auth_header: { type: 'string', label: 'Auth Header Name' },
      content_type: { type: 'select', label: 'Content Type', options: ['application/json', 'text/plain', 'application/x-www-form-urlencoded'] },
      custom_headers: { type: 'textarea', label: 'Custom Headers (Key: Value per line)' },
      include_context: { type: 'boolean', label: 'Include Workflow Context' },
      retry_count: { type: 'number', label: 'Retry Count' },
      retry_delay: { type: 'number', label: 'Retry Delay (s)' },
    },
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
    output: '#6B7280',
    transform: '#06B6D4',
    merge: '#A78BFA',
    delay: '#6366F1',
    switch: '#F59E0B',
    webhook: '#10B981',
    guardrails: '#F43F5E',
    variable: '#D946EF',
    subworkflow: '#0EA5E9',
    batch: '#F472B6',
    custom: '#A3E635',
    webhook_output: '#F97316',
  };

  const typeIcons = {
    input: Download,
    llm: Brain,
    tool: Wrench,
    memory: Database,
    condition: GitBranch,
    loop: Repeat,
    output: FileOutput,
    transform: Wand2,
    merge: Link,
    delay: Timer,
    switch: GitBranch,
    webhook: Anchor,
    guardrails: Shield,
    variable: Package,
    subworkflow: Layers,
    batch: BarChart3,
    custom: Settings,
  };

  const TOOL_PARAMS = {
    web_search: [
      { name: 'query', label: 'Search Query', type: 'string', required: true },
      { name: 'num_results', label: 'Num Results', type: 'number', default: 5 },
      { name: 'scrape', label: 'Scrape URLs for full content', type: 'boolean', default: true },
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
    playwright_browser: [
      { name: 'action', label: 'Action', type: 'select', options: ['goto', 'click', 'type', 'extract', 'screenshot', 'evaluate'], required: true },
      { name: 'url', label: 'URL', type: 'string' },
      { name: 'browser', label: 'Browser', type: 'select', options: ['chrome', 'brave', 'msedge', 'chromium', 'firefox', 'webkit'], default: 'chrome' },
      { name: 'selector', label: 'CSS Selector', type: 'string' },
      { name: 'text', label: 'Text / JS Code', type: 'textarea' },
      { name: 'screenshot', label: 'Screenshot Path', type: 'string' },
      { name: 'wait_seconds', label: 'Wait (s)', type: 'number', default: 3 },
    ],
    list_directory: [
      { name: 'path', label: 'Directory Path', type: 'string' },
      { name: 'pattern', label: 'Glob Pattern', type: 'string' },
    ],
    search_files: [
      { name: 'query', label: 'Search Query', type: 'string', required: true },
      { name: 'path', label: 'Search Directory', type: 'string' },
      { name: 'search_type', label: 'Search Type', type: 'select', options: ['name', 'content'], default: 'name' },
    ],
    json_query: [
      { name: 'data', label: 'JSON Data', type: 'textarea', required: true },
      { name: 'query', label: 'Query Path', type: 'string', required: true },
    ],
    csv_analyze: [
      { name: 'file_path', label: 'CSV File Path', type: 'string', required: true },
      { name: 'operation', label: 'Operation', type: 'select', options: ['summary', 'head', 'filter', 'sort', 'group'], default: 'summary' },
      { name: 'column', label: 'Column Name', type: 'string' },
      { name: 'filter_value', label: 'Filter / Sort Direction', type: 'string' },
      { name: 'limit', label: 'Row Limit', type: 'number', default: 20 },
    ],
    database_query: [
      { name: 'db_path', label: 'Database Path', type: 'string', required: true },
      { name: 'query', label: 'SQL Query', type: 'textarea', required: true },
      { name: 'params', label: 'Bind Parameters (JSON array)', type: 'string' },
    ],
    random_generate: [
      { name: 'type', label: 'Type', type: 'select', options: ['uuid', 'password', 'number', 'string'], default: 'uuid' },
      { name: 'length', label: 'Length', type: 'number', default: 16 },
      { name: 'count', label: 'Count', type: 'number', default: 1 },
    ],
    diff_texts: [
      { name: 'text_a', label: 'Text A', type: 'textarea', required: true },
      { name: 'text_b', label: 'Text B', type: 'textarea', required: true },
      { name: 'context_lines', label: 'Context Lines', type: 'number', default: 3 },
    ],
    hash_data: [
      { name: 'data', label: 'Data to Hash', type: 'string', required: true },
      { name: 'algorithm', label: 'Algorithm', type: 'select', options: ['sha256', 'sha1', 'md5'], default: 'sha256' },
    ],
    rss_read: [
      { name: 'url', label: 'Feed URL', type: 'string', required: true },
      { name: 'max_items', label: 'Max Items', type: 'number', default: 10 },
    ],
    slack_webhook: [
      { name: 'webhook_url', label: 'Webhook URL', type: 'string', required: true },
      { name: 'message', label: 'Message', type: 'string', required: true },
      { name: 'channel', label: 'Channel Override', type: 'string' },
      { name: 'username', label: 'Bot Username', type: 'string', default: 'OllamaFlow' },
    ],
    web_scraper: [
      { name: 'url', label: 'URL to Scrape', type: 'string', required: true },
      { name: 'max_chars', label: 'Max Characters', type: 'number', default: 8000 },
    ],
    youtube_transcript: [
      { name: 'video_url', label: 'YouTube Video URL', type: 'string', required: true },
      { name: 'language', label: 'Language Code', type: 'string', default: 'en' },
    ],
    clipboard_copy: [
      { name: 'text', label: 'Text to Copy', type: 'string', required: true },
    ],
    clipboard_paste: [],
    rate_limiter: [
      { name: 'max_requests', label: 'Max Requests', type: 'number', default: 10 },
      { name: 'window_seconds', label: 'Window (seconds)', type: 'number', default: 60 },
      { name: 'bucket', label: 'Bucket Name', type: 'string', default: 'default' },
    ],
    file_watcher: [
      { name: 'path', label: 'Directory Path', type: 'string' },
      { name: 'pattern', label: 'Glob Pattern', type: 'string', default: '*' },
      { name: 'since_minutes', label: 'Since (minutes)', type: 'number', default: 60 },
    ],
    web_research: [
      { name: 'action', label: 'Action', type: 'select', options: ['search', 'search_and_scrape', 'goto', 'extract', 'screenshot', 'click', 'type', 'evaluate'], required: true },
      { name: 'query', label: 'Search Query / JS Code', type: 'string' },
      { name: 'url', label: 'URL', type: 'string' },
      { name: 'engine', label: 'Search Engine', type: 'select', options: ['google', 'bing', 'duckduckgo', 'brave'], default: 'google' },
      { name: 'max_results', label: 'Max Results', type: 'number', default: 5 },
      { name: 'selector', label: 'CSS Selector', type: 'string' },
      { name: 'screenshot', label: 'Screenshot Path', type: 'string' },
      { name: 'wait_seconds', label: 'Wait (s)', type: 'number', default: 3 },
    ],
    browser_use: [
      { name: 'task', label: 'Task Description', type: 'textarea', required: true },
      { name: 'llm_provider', label: 'LLM Provider', type: 'select', options: ['ollama', 'openai', 'anthropic'], required: true },
      { name: 'llm_model', label: 'Model (blank = default)', type: 'string' },
      { name: 'headless', label: 'Headless Mode', type: 'boolean', default: true },
      { name: 'allowed_domains', label: 'Allowed Domains (comma-separated)', type: 'string' },
      { name: 'max_steps', label: 'Max Steps', type: 'number', default: 25 },
    ],
    crawl4ai: [
      { name: 'action', label: 'Action', type: 'select', options: ['scrape', 'deep_crawl', 'extract_structured'], required: true },
      { name: 'url', label: 'URL', type: 'string', required: true },
      { name: 'max_pages', label: 'Max Pages (deep crawl)', type: 'number', default: 5 },
      { name: 'css_selector', label: 'CSS Selector', type: 'string' },
      { name: 'javascript', label: 'JavaScript to Execute', type: 'textarea' },
      { name: 'cache', label: 'Enable Caching', type: 'boolean', default: true },
      { name: 'fit_markdown', label: 'Filter Noise (fit_markdown)', type: 'boolean', default: true },
    ],
    firecrawl: [
      { name: 'action', label: 'Action', type: 'select', options: ['scrape', 'crawl', 'map', 'search', 'agent'], required: true },
      { name: 'url', label: 'URL', type: 'string' },
      { name: 'query', label: 'Search Query / Agent Prompt', type: 'string' },
      { name: 'limit', label: 'Limit', type: 'number', default: 10 },
      { name: 'formats', label: 'Output Format', type: 'select', options: ['markdown', 'html'], default: 'markdown' },
      { name: 'mode', label: 'Mode', type: 'select', options: ['self_hosted', 'cloud'], default: 'self_hosted' },
    ],
    crawlee: [
      { name: 'action', label: 'Action', type: 'select', options: ['scrape_urls', 'deep_crawl'], required: true },
      { name: 'urls', label: 'URLs (comma-separated)', type: 'string', required: true },
      { name: 'max_requests', label: 'Max Requests', type: 'number', default: 10 },
      { name: 'crawler_type', label: 'Crawler Type', type: 'select', options: ['playwright', 'beautifulsoup'], default: 'playwright' },
      { name: 'proxy_url', label: 'Proxy URL', type: 'string' },
      { name: 'javascript_code', label: 'JavaScript to Execute', type: 'textarea' },
    ],
    markitdown: [
      { name: 'file_path', label: 'File Path', type: 'string' },
      { name: 'input_type', label: 'Input Type', type: 'select', options: ['local_file', 'url'], default: 'local_file' },
      { name: 'url', label: 'URL (for url input type)', type: 'string' },
      { name: 'use_llm', label: 'Use LLM for Image Descriptions', type: 'boolean', default: false },
      { name: 'llm_model', label: 'LLM Model (for images)', type: 'string' },
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

      if (p.type === 'boolean') {
        return (
          <div key={p.name} className="mb-2 flex items-center justify-between">
            <label className="text-xs text-gray-400">{p.label}</label>
            <button
              onClick={() => updateParam(!value)}
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
    });
  };

  return (
    <div className="w-72 bg-[#141414] border-l border-[#333] flex flex-col shrink-0 overflow-hidden">
      <div className="px-4 py-3 border-b border-[#333] flex items-center justify-between">
        <div className="flex items-center gap-2">
          {(() => {
            const Icon = typeIcons[type];
            return Icon ? <Icon className="w-3.5 h-3.5" style={{ color: typeColors[type] }} /> : null;
          })()}
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
