import { useState } from "react";
import "./App.css";
import { ConversationView } from "./views/ConversationView";
import { ReviewView } from "./views/ReviewView";
import { MinimalPairDrill } from "./components/MinimalPairDrill";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ToastContainer } from "./components/Toast";
import { ConnectionBanner } from "./components/ConnectionBanner";
import { useTheme } from "./hooks/useTheme";

type Tab = "conversation" | "review" | "listening";

// ponytail: build-time flag only (no runtime toggle needed) -- public deploy
// has no Voice Conversation backend, so ConversationView/useSessionState must
// never mount there (its SSE hook would just spin against a missing endpoint).
const PUBLIC_MODE = import.meta.env.VITE_PUBLIC_MODE === "true";

// ponytail: presentational only, no props/state -- not worth a named file or test.
function Brand() {
  return (
    <div className="brand">
      <svg className="brand-mark" width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <path
          d="M11 2.4a8.6 8.6 0 1 1-5.6 15.1L2.6 19l1.1-3.1A8.6 8.6 0 0 1 11 2.4Z"
          stroke="var(--accent)"
          strokeWidth="1.4"
          fill="none"
        />
        <circle cx="11" cy="11" r="2.4" fill="var(--accent)" />
      </svg>
      <h1 className="brand-name">Spanish Companion</h1>
    </div>
  );
}

function ThemeToggle({ theme, onToggle }: { theme: "light" | "dark"; onToggle: () => void }) {
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? (
        <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden="true">
          <circle cx="8.5" cy="8.5" r="3.6" stroke="currentColor" strokeWidth="1.3" />
          <path
            d="M8.5 1.4v1.8M8.5 13.8v1.8M15.6 8.5h-1.8M3.2 8.5H1.4M13.4 3.6l-1.3 1.3M4.9 12.1l-1.3 1.3M13.4 13.4l-1.3-1.3M4.9 4.9 3.6 3.6"
            stroke="currentColor"
            strokeWidth="1.3"
            strokeLinecap="round"
          />
        </svg>
      ) : (
        <svg width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden="true">
          <path
            d="M14.5 10.1a6 6 0 0 1-7.6-7.6A6.5 6.5 0 1 0 14.5 10.1Z"
            stroke="currentColor"
            strokeWidth="1.3"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </button>
  );
}

function App() {
  const [tab, setTab] = useState<Tab>("conversation");
  const { theme, toggleTheme } = useTheme();

  if (PUBLIC_MODE) {
    return (
      <>
        <header className="tabs">
          <Brand />
          <div className="tabs-right">
            <nav>
              <button className={tab === "review" ? "active" : ""} onClick={() => setTab("review")}>
                Review
              </button>
              <button className={tab === "listening" ? "active" : ""} onClick={() => setTab("listening")}>
                Listening
              </button>
            </nav>
            <ThemeToggle theme={theme} onToggle={toggleTheme} />
          </div>
        </header>
        <ConnectionBanner />
        <main>
          <ErrorBoundary key={tab}>{tab === "listening" ? <MinimalPairDrill /> : <ReviewView />}</ErrorBoundary>
        </main>
        <ToastContainer />
      </>
    );
  }

  return (
    <>
      <header className="tabs">
        <Brand />
        <div className="tabs-right">
          <nav>
            <button className={tab === "conversation" ? "active" : ""} onClick={() => setTab("conversation")}>
              Conversation
            </button>
            <button className={tab === "review" ? "active" : ""} onClick={() => setTab("review")}>
              Review
            </button>
            <button className={tab === "listening" ? "active" : ""} onClick={() => setTab("listening")}>
              Listening
            </button>
          </nav>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
        </div>
      </header>
      <ConnectionBanner />

      <main>
        <ErrorBoundary key={tab}>
          {tab === "conversation" ? <ConversationView /> : tab === "review" ? <ReviewView /> : <MinimalPairDrill />}
        </ErrorBoundary>
      </main>
      <ToastContainer />
    </>
  );
}

export default App;
