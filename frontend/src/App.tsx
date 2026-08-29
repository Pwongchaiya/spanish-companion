import { useState } from "react";
import "./App.css";
import { ConversationView } from "./views/ConversationView";
import { ReviewView } from "./views/ReviewView";

type Tab = "conversation" | "review";

function App() {
  const [tab, setTab] = useState<Tab>("conversation");

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
