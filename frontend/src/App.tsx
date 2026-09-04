import { useState } from "react";
import "./App.css";
import { ConversationView } from "./views/ConversationView";
import { ReviewView } from "./views/ReviewView";

type Tab = "conversation" | "review";

// ponytail: build-time flag only (no runtime toggle needed) -- public deploy
// has no Voice Conversation backend, so ConversationView/useSessionState must
// never mount there (its SSE hook would just spin against a missing endpoint).
const PUBLIC_MODE = import.meta.env.VITE_PUBLIC_MODE === "true";

function App() {
  const [tab, setTab] = useState<Tab>("conversation");

  if (PUBLIC_MODE) {
    return (
      <>
        <header className="tabs">
          <h1>Spanish Companion</h1>
        </header>
        <main>
          <ReviewView />
        </main>
      </>
    );
  }

  return (
    <>
      <header className="tabs">
        <h1>Spanish Companion</h1>
        <nav>
          <button className={tab === "conversation" ? "active" : ""} onClick={() => setTab("conversation")}>
            Conversation
          </button>
          <button className={tab === "review" ? "active" : ""} onClick={() => setTab("review")}>
            Review
          </button>
        </nav>
      </header>

      <main>{tab === "conversation" ? <ConversationView /> : <ReviewView />}</main>
    </>
  );
}

export default App;
