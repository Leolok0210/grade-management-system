import { useState, useRef, useEffect } from "react";
import type { ChatMessage, DataCard } from "../../types";
import { ResultCard } from "./ResultCard";

interface ChatWindowProps {
  messages: ChatMessage[];
  loading: boolean;
  activeDataCard: DataCard | null;
  onSend: (msg: string) => void;
  onClearDataCard: () => void;
}

export function ChatWindow({ messages, loading, activeDataCard, onSend, onClearDataCard }: ChatWindowProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSend(input.trim());
      setInput("");
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.headerTitle}>成績管理助手</h2>
      </div>

      {/* Data Card Panel */}
      {activeDataCard && (
        <div style={styles.dataCardPanel}>
          <ResultCard card={activeDataCard} onClose={onClearDataCard} />
        </div>
      )}

      {/* Messages */}
      <div style={styles.messages}>
        {messages.length === 0 && (
          <div style={styles.empty}>
            <p>您好！我是成績管理AI助手。</p>
            <p>您可以告訴我任何成績相關的需求，例如：</p>
            <ul style={styles.examples}>
              <li>「幫我登記三年二班數學小考成績」</li>
              <li>「查看王小明的平時成績」</li>
              <li>「產生這學期的成績草榜」</li>
              <li>「列出各班前五名」</li>
            </ul>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} style={msg.role === "user" ? styles.userMsg : styles.assistantMsg}>
            <div style={msg.role === "user" ? styles.userBubble : styles.assistantBubble}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={styles.assistantMsg}>
            <div style={styles.assistantBubble}>
              <span style={styles.typing}>思考中...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} style={styles.inputBar}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="輸入您的需求..."
          style={styles.inputField}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} style={styles.sendBtn}>
          發送
        </button>
      </form>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100vh",
    background: "#f5f6fa",
  },
  header: {
    padding: "16px 24px",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "#fff",
  },
  headerTitle: { fontSize: 20, fontWeight: 600, margin: 0 },
  dataCardPanel: {
    padding: "16px 24px",
    background: "#fff",
    borderBottom: "1px solid #eee",
  },
  messages: {
    flex: 1,
    overflowY: "auto" as const,
    padding: "24px",
  },
  empty: {
    textAlign: "center" as const,
    color: "#888",
    padding: "40px 20px",
  },
  examples: {
    listStyle: "none" as const,
    padding: 0,
    textAlign: "left" as const,
    maxWidth: 400,
    margin: "16px auto",
  },
  userMsg: { display: "flex", justifyContent: "flex-end" as const, marginBottom: 12 },
  assistantMsg: { display: "flex", justifyContent: "flex-start" as const, marginBottom: 12 },
  userBubble: {
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "#fff",
    padding: "10px 16px",
    borderRadius: 12,
    maxWidth: "70%",
    fontSize: 15,
  },
  assistantBubble: {
    background: "#fff",
    color: "#333",
    padding: "10px 16px",
    borderRadius: 12,
    maxWidth: "70%",
    fontSize: 15,
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  },
  typing: { color: "#888" },
  inputBar: {
    display: "flex",
    gap: 8,
    padding: "16px 24px",
    background: "#fff",
    borderTop: "1px solid #eee",
  },
  inputField: {
    flex: 1,
    padding: "12px 16px",
    borderRadius: 8,
    border: "1px solid #ddd",
    fontSize: 15,
    outline: "none",
  },
  sendBtn: {
    padding: "12px 24px",
    borderRadius: 8,
    border: "none",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "#fff",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
  },
};