import { create } from "zustand";

export interface Toast {
  id: number;
  message: string;
}

interface ToastStore {
  toasts: Toast[];
  addToast: (message: string) => void;
  dismissToast: (id: number) => void;
}

// ponytail: incrementing counter is enough for id uniqueness in a
// single-tab session -- no crypto.randomUUID needed.
let nextId = 1;

export const useToastStore = create<ToastStore>()((set) => ({
  toasts: [],
  addToast: (message) =>
    set((s) => ({ toasts: [...s.toasts, { id: nextId++, message }] })),
  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
