import { useMemo, useState } from "react";
import "./styles.css";

const navItems = [
  { id: "overview", label: "Overview" },
  { id: "customers", label: "Customers", badge: "24" },
  { id: "risk", label: "Risk", badge: "7" },
  { id: "campaigns", label: "Campaigns" },
  { id: "agent", label: "AI Agent" },
];

const kpis = [
  { label: "Managed Deposits", value: "S$48.2M", trend: "+5.4% this week" },
  { label: "Active Customers", value: "12,804", trend: "+186 today" },
  { label: "Pending Reviews", value: "41", trend: "-8 from yesterday" },
  { label: "Agent Resolution", value: "82%", trend: "+9% uplift" },
];

const portfolioEvents = [
  {
    title: "Travel spend pattern detected",
    detail: "Card transactions increased 3x in 9 days. FX card offer triggered.",
    time: "2h ago",
  },
  {
    title: "Salary credit matched",
    detail: "Income consistency score now qualifies for smart-credit pre-check.",
    time: "4h ago",
  },
  {
    title: "Savings goal reached",
    detail: "Round-up behavior hit target. Auto-invest education flow suggested.",
    time: "8h ago",
  },
];

const queueItems = [
  {
    customer: "Alicia Tan",
    request: "KYC refresh and document mismatch",
    amount: "S$120K",
    priority: "High",
  },
  {
    customer: "Harith Ismail",
    request: "Unusual transfer behavior",
    amount: "S$21K",
    priority: "High",
  },
  {
    customer: "Darren Lim",
    request: "Card dispute follow-up",
    amount: "S$3.2K",
    priority: "Medium",
  },
  {
    customer: "Jia En Ong",
    request: "Account recovery verification",
    amount: "S$0.9K",
    priority: "Low",
  },
];

const campaignIdeas = [
  {
    title: "Micro-saving habit nudge",
    body: "Target users with stable inflow and low transfer-out ratio for 14 days.",
    tag: "AI Suggested",
  },
  {
    title: "Smart card switch pitch",
    body: "Recommend no-FX card to users with repeated travel merchant activity.",
    tag: "Live Segment",
  },
  {
    title: "Retention concierge callback",
    body: "Escalate high-balance users after two unresolved support interactions.",
    tag: "Priority",
  },
];

const initialChat = [
  {
    role: "agent",
    author: "GXS Copilot",
    time: "09:41",
    text: "Morning brief: 7 high-risk profiles need review. I prepared a ranked queue.",
  },
  {
    role: "partner",
    author: "Relationship Lead",
    time: "09:43",
    text: "Prioritize profiles with transfer velocity spikes and low KYC confidence.",
  },
  {
    role: "agent",
    author: "GXS Copilot",
    time: "09:44",
    text: "Done. I flagged Alicia Tan and Harith Ismail, and drafted customer-safe outreach.",
  },
];

const quickActions = [
  "Draft outreach for Alicia Tan",
  "Summarize top risk drivers",
  "Create compliance handoff note",
];

function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState(initialChat);

  const highPriorityCount = useMemo(
    () => queueItems.filter((item) => item.priority === "High").length,
    [],
  );

  const handleSend = (event) => {
    event.preventDefault();
    const cleaned = draft.trim();
    if (!cleaned) {
      return;
    }

    const responsePreview = cleaned.length > 60 ? `${cleaned.slice(0, 60)}...` : cleaned;

    setMessages((current) => [
      ...current,
      {
        role: "partner",
        author: "You",
        time: "Now",
        text: cleaned,
      },
      {
        role: "agent",
        author: "GXS Copilot",
        time: "Now",
        text: `Acknowledged. I can execute next actions for "${responsePreview}" with compliance-safe language.`,
      },
    ]);

    setDraft("");
  };

  return (
    <div className="partner-page">
      <div className="aurora aurora-one" />
      <div className="aurora aurora-two" />

      <div className="app-frame">
        <aside className="sidebar panel reveal">
          <div className="brand-block">
            <span className="brand-led" aria-hidden="true" />
            <div>
              <p className="brand-eyebrow">GXS Partner</p>
              <h1>Agent Workspace</h1>
            </div>
          </div>

          <nav className="rail-nav" aria-label="Partner modules">
            {navItems.map((item) => (
              <button
                type="button"
                key={item.id}
                className={item.id === activeTab ? "rail-link active" : "rail-link"}
                onClick={() => setActiveTab(item.id)}
              >
                <span>{item.label}</span>
                {item.badge ? <span className="nav-badge">{item.badge}</span> : null}
              </button>
            ))}
          </nav>

          <div className="sidebar-card">
            <p className="sidebar-kicker">Live alerts</p>
            <h3>{highPriorityCount} high-priority reviews</h3>
            <p>Customer identity and transfer-risk checks are waiting for your approval.</p>
            <button type="button">Open verification queue</button>
          </div>
        </aside>

        <main className="workspace">
          <header className="workspace-top panel reveal">
            <div>
              <p className="kicker">GXS Banking Partner Console</p>
              <h2>Customer desk, risk operations, and AI copilot</h2>
            </div>
            <div className="top-actions">
              <span className="status-pill">Sandbox mode</span>
              <button type="button">Sync accounts</button>
            </div>
          </header>

          <section className="kpi-grid">
            {kpis.map((item) => (
              <article className="panel reveal metric-card" key={item.label}>
                <p>{item.label}</p>
                <h3>{item.value}</h3>
                <span>{item.trend}</span>
              </article>
            ))}
          </section>

          <section className="main-grid">
            <article className="panel reveal customer-panel">
              <header className="section-head">
                <div>
                  <p className="kicker">Customer 360</p>
                  <h3>Primary profile: Alicia Tan</h3>
                </div>
                <button type="button">View full profile</button>
              </header>

              <div className="customer-identity">
                <div>
                  <span>Segment</span>
                  <strong>Affluent Digital Saver</strong>
                </div>
                <div>
                  <span>Portfolio value</span>
                  <strong>S$284,900</strong>
                </div>
                <div>
                  <span>Risk score</span>
                  <strong>62 / 100</strong>
                </div>
              </div>

              <ul className="event-list">
                {portfolioEvents.map((event) => (
                  <li key={event.title}>
                    <div>
                      <h4>{event.title}</h4>
                      <p>{event.detail}</p>
                    </div>
                    <span>{event.time}</span>
                  </li>
                ))}
              </ul>
            </article>

            <article className="panel reveal chat-panel">
              <header className="section-head">
                <div>
                  <p className="kicker">AI Agent Desk</p>
                  <h3>GXS Copilot live conversation</h3>
                </div>
                <button type="button">Open full thread</button>
              </header>

              <div className="chat-stream" aria-live="polite">
                {messages.map((message, index) => (
                  <article className={`chat-bubble ${message.role}`} key={`${message.author}-${index}`}>
                    <p className="chat-author">
                      {message.author}
                      <span>{message.time}</span>
                    </p>
                    <p>{message.text}</p>
                  </article>
                ))}
              </div>

              <form className="chat-composer" onSubmit={handleSend}>
                <input
                  type="text"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Ask agent to draft, summarize, or prioritize..."
                  aria-label="Agent prompt"
                />
                <button type="submit">Send</button>
              </form>

              <div className="action-chips">
                {quickActions.map((action) => (
                  <button type="button" key={action} onClick={() => setDraft(action)}>
                    {action}
                  </button>
                ))}
              </div>
            </article>
          </section>

          <section className="queue-grid">
            <article className="panel reveal queue-panel">
              <header className="section-head">
                <div>
                  <p className="kicker">Verification Queue</p>
                  <h3>Pending customer checks</h3>
                </div>
                <button type="button">Export list</button>
              </header>

              <div className="queue-list">
                {queueItems.map((item) => (
                  <article className="queue-row" key={`${item.customer}-${item.request}`}>
                    <div>
                      <h4>{item.customer}</h4>
                      <p>{item.request}</p>
                    </div>
                    <strong>{item.amount}</strong>
                    <span className={`priority ${item.priority.toLowerCase()}`}>{item.priority}</span>
                  </article>
                ))}
              </div>
            </article>

            <article className="panel reveal campaign-panel">
              <header className="section-head">
                <div>
                  <p className="kicker">Growth Engine</p>
                  <h3>AI-assisted campaign ideas</h3>
                </div>
                <button type="button">Launch workflow</button>
              </header>

              <div className="campaign-list">
                {campaignIdeas.map((idea) => (
                  <article key={idea.title}>
                    <p className="tag">{idea.tag}</p>
                    <h4>{idea.title}</h4>
                    <p>{idea.body}</p>
                  </article>
                ))}
              </div>
            </article>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
