'use client';

import { useState, useEffect, createContext, useContext, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastContextType {
  toast: (type: ToastType, title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

const icons: Record<ToastType, any> = {
  success: CheckCircle2,
  error: AlertTriangle,
  warning: AlertTriangle,
  info: Info,
};

const styles: Record<ToastType, string> = {
  success: 'border-diya-resolved/30 bg-diya-resolved-dim',
  error: 'border-diya-conflict/30 bg-diya-conflict-dim',
  warning: 'border-diya-pending/30 bg-diya-pending-dim',
  info: 'border-diya-border bg-diya-card',
};

const iconStyles: Record<ToastType, string> = {
  success: 'text-diya-resolved',
  error: 'text-diya-conflict',
  warning: 'text-diya-pending',
  info: 'text-diya-text-secondary',
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = `toast-${Date.now()}`;
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => {
          const Icon = icons[t.type];
          return (
            <div
              key={t.id}
              className={cn(
                'pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-lg border shadow-xl backdrop-blur-md min-w-[280px] max-w-[380px] animate-slide-up',
                styles[t.type]
              )}
            >
              <Icon className={cn('w-4 h-4 mt-0.5 flex-shrink-0', iconStyles[t.type])} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{t.title}</p>
                {t.message && (
                  <p className="text-xs text-diya-text-secondary mt-0.5">{t.message}</p>
                )}
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="w-5 h-5 flex items-center justify-center rounded hover:bg-white/10 flex-shrink-0"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
