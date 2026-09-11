import { create } from "zustand";

export interface Toast {
  id: number;
  message: string;
  subMessage?: string;
  count: number;
  retry?: () => void;
}

export interface AddToastOptions {
  subMessage?: string;
  retry?: () => void;
}

interface ToastStore {
  toasts: Toast[];
  addToast: (message: string, opts?: AddToastOptions) => void;
  dismissToast: (id: number) => void;
}

// ponytail: incrementing counter is enough for id uniqueness in a
// single-tab session -- no crypto.randomUUID needed.
let nextId = 1;

export const useToastStore = create<ToastStore>()((set) => ({
  toasts: [],
  // Dedupe by message: a repeated identical failure bumps the existing
  // toast's count instead of stacking a new one (the "4 stacked toasts"
  // bug from the Aliento error-handling mockup). subMessage/retry refresh
  // to the latest call's values so "Try again" always retries the most
  // recent attempt.
  addToast: (message, opts) =>
    set((s) => {
      const existing = s.toasts.find((t) => t.message === message);
      if (existing) {
        return {
          toasts: s.toasts.map((t) =>
            t.id === existing.id
              ? { ...t, count: t.count + 1, subMessage: opts?.subMessage, retry: opts?.retry }
              : t,
          ),
        };
      }
      return {
        toasts: [...s.toasts, { id: nextId++, message, subMessage: opts?.subMessage, retry: opts?.retry, count: 1 }],
      };
    }),
  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
