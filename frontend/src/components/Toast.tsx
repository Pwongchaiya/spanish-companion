import { useToastStore } from "../state/toastStore";
import "./shared.css";

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const dismissToast = useToastStore((s) => s.dismissToast);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <div key={toast.id} className="toast" role="alert">
          <span>{toast.message}</span>
          {toast.count > 1 && <span className="toast-count">{toast.count}×</span>}
          <button className="toast-dismiss" onClick={() => dismissToast(toast.id)} aria-label="Dismiss">
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
