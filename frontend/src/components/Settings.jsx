import React, { useState, useEffect } from 'react';
import { X, Save, Key, Cpu, Globe, Search } from 'lucide-react';
import axios from 'axios';

export default function Settings({ onClose }) {
  const [settings, setSettings] = useState({
    provider: 'ollama',
    groq_api_key: '',
    groq_model: 'llama-3.3-70b-versatile',
    ollama_base: 'http://localhost:11434',
    default_model: 'llama3.1:8b',
    search_provider: 'auto',
    brave_api_key: '',
    searxng_url: '',
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const resp = await axios.get('/api/settings');
      setSettings(prev => ({ ...prev, ...resp.data.settings }));
    } catch (err) {
      console.error('Failed to load settings');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      await axios.post('/api/settings', { settings });
      setMessage('Settings saved!');
    } catch (err) {
      setMessage('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const groqModels = [
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'gemma2-9b-it',
    'mixtral-8x7b-32768',
    'meta-llama/llama-4-scout-17b-16e-instruct',
  ];

  const searchProviders = [
    { id: 'auto', label: 'Auto (Recommended)', desc: 'Brave + SearXNG + Bing + DuckDuckGo fallback' },
    { id: 'brave', label: 'Brave Search', desc: '2,000 free queries/month' },
    { id: 'searxng', label: 'SearXNG', desc: 'Self-hosted, unlimited' },
    { id: 'duckduckgo', label: 'DuckDuckGo', desc: 'Free, no API key' },
  ];

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#141414] border border-[#333] rounded-xl w-[520px] max-h-[80vh] overflow-hidden flex flex-col">
        <div className="px-5 py-4 border-b border-[#333] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-blue-500" />
            <span className="text-sm font-semibold text-white">Settings</span>
          </div>
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-white transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-6">
          <div>
            <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1">
              <Cpu className="w-3 h-3" /> AI Provider
            </p>
            <div className="flex gap-2">
              {['ollama', 'groq'].map((p) => (
                <button
                  key={p}
                  onClick={() => setSettings(prev => ({ ...prev, provider: p }))}
                  className={`flex-1 px-3 py-2 rounded-lg border text-xs font-medium transition ${
                    settings.provider === p
                      ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                      : 'bg-[#0f0f0f] border-[#333] text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {p === 'ollama' ? 'Ollama (Local)' : 'Groq (Cloud)'}
                </button>
              ))}
            </div>
          </div>

          {settings.provider === 'ollama' && (
            <div>
              <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2">Ollama URL</p>
              <input
                type="text"
                value={settings.ollama_base}
                onChange={(e) => setSettings(prev => ({ ...prev, ollama_base: e.target.value }))}
                className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-[10px] text-gray-500 mt-1">Default: http://localhost:11434</p>
            </div>
          )}

          {settings.provider === 'groq' && (
            <>
              <div>
                <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                  <Key className="w-3 h-3" /> API Key
                </p>
                <input
                  type="password"
                  value={settings.groq_api_key}
                  onChange={(e) => setSettings(prev => ({ ...prev, groq_api_key: e.target.value }))}
                  placeholder="gsk_..."
                  className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                />
                <p className="text-[10px] text-gray-500 mt-1">
                  Get your key at{' '}
                  <a href="https://console.groq.com" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                    console.groq.com
                  </a>
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2">Model</p>
                <select
                  value={settings.groq_model}
                  onChange={(e) => setSettings(prev => ({ ...prev, groq_model: e.target.value }))}
                  className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  {groqModels.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            </>
          )}

          <div className="w-full h-px bg-[#333]" />

          <div>
            <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1">
              <Search className="w-3 h-3" /> Web Search Provider
            </p>
            <div className="space-y-2">
              {searchProviders.map((sp) => (
                <button
                  key={sp.id}
                  onClick={() => setSettings(prev => ({ ...prev, search_provider: sp.id }))}
                  className={`w-full px-3 py-2 rounded-lg border text-left transition ${
                    settings.search_provider === sp.id
                      ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                      : 'bg-[#0f0f0f] border-[#333] text-gray-400 hover:border-gray-500'
                  }`}
                >
                  <div className="text-xs font-medium">{sp.label}</div>
                  <div className="text-[10px] opacity-60 mt-0.5">{sp.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {(settings.search_provider === 'auto' || settings.search_provider === 'brave') && (
            <div>
              <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <Key className="w-3 h-3" /> Brave Search API Key
              </p>
              <input
                type="password"
                value={settings.brave_api_key}
                onChange={(e) => setSettings(prev => ({ ...prev, brave_api_key: e.target.value }))}
                placeholder="BSA..."
                className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-[10px] text-gray-500 mt-1">
                Optional. 2,000 free queries/month. Get key at{' '}
                <a href="https://brave.com/search/api/" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                  brave.com/search/api
                </a>
              </p>
            </div>
          )}

          {(settings.search_provider === 'auto' || settings.search_provider === 'searxng') && (
            <div>
              <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <Globe className="w-3 h-3" /> SearXNG Instance URL
              </p>
              <input
                type="text"
                value={settings.searxng_url}
                onChange={(e) => setSettings(prev => ({ ...prev, searxng_url: e.target.value }))}
                placeholder="http://localhost:8888"
                className="w-full bg-[#0f0f0f] border border-[#333] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-[10px] text-gray-500 mt-1">
                Optional. Self-hosted meta-search engine. Aggregates Google, Bing, DuckDuckGo.
              </p>
            </div>
          )}
        </div>

        <div className="px-5 py-3 border-t border-[#333] flex items-center justify-between">
          <p className="text-xs text-green-400">{message}</p>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg border border-[#333] text-xs text-gray-400 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium hover:bg-blue-500 transition disabled:opacity-50 flex items-center gap-1"
            >
              <Save className="w-3 h-3" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
