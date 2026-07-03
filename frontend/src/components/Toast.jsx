import React, { useEffect, useState } from 'react';

const TOAST_STYLES = {
  success: 'bg-green-600',
  error: 'bg-red-600',
  info: 'bg-blue-600',
  warning: 'bg-yellow-600',
};

let toastId = 0;
let listeners = [];

export function showToast(message, type = 'info', duration = 3000) {
  const id = ++toastId;
  const toast = { id, message, type, duration };
  listeners.forEach((fn) => fn(toast));
  return id;
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handler = (toast) => {
      setToasts((prev) => [...prev, toast]);
      if (toast.duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== toast.id));
        }, toast.duration);
      }
    };
    listeners.push(handler);
    return () => {
      listeners = listeners.filter((fn) => fn !== handler);
    };
  }, []);

  const dismiss = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`${TOAST_STYLES[toast.type] || TOAST_STYLES.info} text-white px-4 py-3 rounded-lg shadow-lg flex items-center justify-between animate-slide-in`}
        >
          <span className="text-sm">{toast.message}</span>
          <button
            onClick={() => dismiss(toast.id)}
            className="ml-3 text-white/70 hover:text-white text-lg leading-none"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
