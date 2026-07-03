import React from 'react';

const shortcuts = [
  { keys: ['Ctrl', 'S'], description: 'Save workflow' },
  { keys: ['Ctrl', 'Z'], description: 'Undo' },
  { keys: ['Ctrl', 'Y'], description: 'Redo' },
  { keys: ['Ctrl', 'Shift', 'Z'], description: 'Redo (alternative)' },
  { keys: ['Ctrl', 'D'], description: 'Duplicate selected node' },
  { keys: ['Delete'], description: 'Delete selected node/edge' },
  { keys: ['?'], description: 'Show this help' },
];

export default function ShortcutModal({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]" onClick={onClose}>
      <div
        className="bg-[#1a1a1a] border border-[#333] rounded-xl p-6 w-[400px] max-h-[80vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Keyboard Shortcuts</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button>
        </div>
        <div className="space-y-3">
          {shortcuts.map((s, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-[#333] last:border-0">
              <span className="text-gray-300 text-sm">{s.description}</span>
              <div className="flex gap-1">
                {s.keys.map((key, j) => (
                  <kbd
                    key={j}
                    className="px-2 py-1 bg-[#2a2a2a] border border-[#444] rounded text-xs text-gray-200 font-mono"
                  >
                    {key}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="text-gray-500 text-xs mt-4 text-center">
          Press <kbd className="px-1 py-0.5 bg-[#2a2a2a] border border-[#444] rounded text-xs">?</kbd> to toggle this panel
        </p>
      </div>
    </div>
  );
}
