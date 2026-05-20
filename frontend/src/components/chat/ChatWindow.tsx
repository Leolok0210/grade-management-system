import { useEffect, useRef, useState } from "react";
import { useChat } from "../../hooks/useChat";
import { chatApi } from "../../api/client";
import { ResultCard } from "./ResultCard";

export function ChatWindow() {
  const {
    messages,
    setMessages,
    loading,
    activeDataCard,
    conversations,
    sendMessage,
    clearChat,
    setActiveDataCard,
    loadConversations,
    loadConversation,
  } = useChat();

  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [welcomeHints, setWelcomeHints] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    chatApi.system.getConfig().then(({ data }) => {
      setWelcomeHints(data.welcome_hints || []);
    }).catch(() => {});
  }, []);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={styles.container}>
      {/* Sidebar */}
      <div style={{ ...styles.sidebar, display: sidebarOpen ? "block" : "none" }}>
        <div style={styles.sidebarHeader}>
          <span style={styles.sidebarTitle}>對話記錄</span>
          <button onClick={() => setSidebarOpen(false)} style={styles.sidebarClose}>✕</button>
        </div>
        <button onClick={clearChat} style={styles.newChatBtn}>+ 新對話</button>
        <div style={styles.convList}>
          {conversations.length === 0 && (
            <div style={styles.emptyConv}>尚無對話</div>
          )}
          {conversations.map((c) => (
            <button
              key={c.id}
              style={styles.convItem}
              onClick={() => { loadConversation(c.id); setSidebarOpen(false); }}
            >
              <span style={styles.convPreview}>{c.preview || "（空白對話）"}</span>
              {c.updated_at && (
                <span style={styles.convDate}>
                  {new Date(c.updated_at).toLocaleDateString("zh-TW")}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main */}
      <div style={styles.main}>
        {/* Top bar */}
        <div style={styles.topBar}>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} style={styles.menuBtn}>☰</button>
          <span style={styles.topTitle}>成績管理助手</span>
          <span style={{ width: 36 }} />
        </div>

        {/* Messages */}
        <div style={styles.messagesArea}>
          {messages.length === 0 && (
            <div style={styles.welcome}>
              <div style={styles.welcomeIcon}>🎓</div>
              <h2>氹仔坊眾學校 成績管理助手</h2>
              <p>你可以問我：</p>
              <ul style={styles.hintList}>
                {welcomeHints.map((hint) => (
                  <li key={hint}>{hint}</li>
                ))}
              </ul>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} style={msg.role === "user" ? styles.userRow : styles.assistantRow}>
              <div style={msg.role === "user" ? styles.userBubble : styles.assistantBubble}>
                {msg.content}
                {msg._status && (
                  <span style={styles.typing}>{msg._status}</span>
                )}
                {!msg.content && !msg._status && msg.role === "assistant" && loading && (
                  <span style={styles.typing}>思考中...</span>
                )}
              </div>
              {msg.dataCards && msg.dataCards.length > 0 && (
                <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
                  {msg.dataCards.map((card, idx) => (
                    <ResultCard
                      key={idx}
                      card={card}
                      onClose={() => {
                        setMessages((prev) =>
                          prev.map((m) =>
                            m.id === msg.id
                              ? { ...m, dataCards: m.dataCards?.filter((_, i) => i !== idx) }
                              : m
                          )
                        );
                      }}
                    />
                  ))}
                </div>
              )}
              {!msg.dataCards?.length && msg.dataCard && (
                <div style={{ marginTop: 8 }}>
                  <ResultCard
                    card={msg.dataCard}
                    onClose={() => {
                      setMessages((prev) =>
                        prev.map((m) => m.id === msg.id ? { ...m, dataCard: undefined } : m)
                      );
                    }}
                  />
                </div>
              )}
            </div>
          ))}
          {loading && messages[messages.length - 1]?.role === "user" && (
            <div style={styles.assistantRow}>
              <div style={styles.assistantBubble}>
                <span style={styles.typing}>思考中...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Active data card */}
        {activeDataCard && (
          <div style={styles.cardArea}>
            <ResultCard card={activeDataCard} onClose={() => setActiveDataCard(null)} />
          </div>
        )}

        {/* Input */}
        <div style={styles.inputArea}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="輸入訊息..."
            style={styles.textarea}
            rows={1}
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()} style={styles.sendBtn}>
            發送
          </button>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { display: "flex", height: "100vh", background: "#f0f2f5" },
  sidebar: {
    width: 260,
    background: "#fff",
    borderRight: "1px solid #eee",
    display: "flex",
    flexDirection: "column",
  },
  sidebarHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    borderBottom: "1px solid #eee",
  },
  sidebarTitle: { fontSize: 15, fontWeight: 600 },
  sidebarClose: { background: "none", border: "none", fontSize: 16, cursor: "pointer", color: "#888" },
  newChatBtn: {
    margin: "8px 12px",
    padding: "8px",
    background: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 13,
  },
  convList: { flex: 1, overflowY: "auto", padding: "4px 0" },
  emptyConv: { padding: 16, color: "#aaa", fontSize: 13, textAlign: "center" as const },
  convItem: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "flex-start",
    width: "100%",
    padding: "10px 16px",
    background: "none",
    border: "none",
    borderBottom: "1px solid #f5f5f5",
    cursor: "pointer",
    textAlign: "left" as const,
  },
  convPreview: { fontSize: 13, color: "#333", lineHeight: 1.4 },
  convDate: { fontSize: 11, color: "#aaa", marginTop: 2 },
  main: { flex: 1, display: "flex", flexDirection: "column", minWidth: 0 },
  topBar: {
    display: "flex",
    alignItems: "center",
    padding: "10px 16px",
    background: "#fff",
    borderBottom: "1px solid #eee",
  },
  menuBtn: { background: "none", border: "none", fontSize: 20, cursor: "pointer", marginRight: 12, color: "#555" },
  topTitle: { fontSize: 16, fontWeight: 600 },
  messagesArea: { flex: 1, overflowY: "auto", padding: "16px 20px" },
  welcome: { textAlign: "center" as const, padding: "60px 20px", color: "#666" },
  welcomeIcon: { fontSize: 48, marginBottom: 12 },
  hintList: { textAlign: "left" as const, display: "inline-block", color: "#888", fontSize: 14, lineHeight: 2 },
  userRow: { display: "flex", justifyContent: "flex-end", marginBottom: 12 },
  assistantRow: { display: "flex", justifyContent: "flex-start", marginBottom: 12 },
  userBubble: {
    background: "#4f46e5",
    color: "#fff",
    padding: "10px 14px",
    borderRadius: "12px 12px 2px 12px",
    maxWidth: "70%",
    fontSize: 14,
    lineHeight: 1.5,
    whiteSpace: "pre-wrap" as const,
  },
  assistantBubble: {
    background: "#fff",
    color: "#333",
    padding: "10px 14px",
    borderRadius: "12px 12px 12px 2px",
    maxWidth: "70%",
    fontSize: 14,
    lineHeight: 1.5,
    whiteSpace: "pre-wrap" as const,
    boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
  },
  typing: { color: "#999", fontSize: 13 },
  cardArea: { padding: "0 20px 8px" },
  inputArea: {
    display: "flex",
    gap: 8,
    padding: "12px 20px",
    background: "#fff",
    borderTop: "1px solid #eee",
  },
  textarea: {
    flex: 1,
    padding: "10px 12px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: 14,
    resize: "none",
    fontFamily: "inherit",
    outline: "none",
  },
  sendBtn: {
    padding: "10px 20px",
    background: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 14,
    fontWeight: 500,
  },
};
