import { useAuth } from "./hooks/useAuth";
import { useChat } from "./hooks/useChat";
import { LoginScreen } from "./components/auth/LoginScreen";
import { ChatWindow } from "./components/chat/ChatWindow";

function App() {
  const { user, isAuthenticated, login, logout } = useAuth();
  const { messages, loading, activeDataCard, sendMessage, clearChat, setActiveDataCard } = useChat();

  if (!isAuthenticated) {
    return <LoginScreen onLogin={login} />;
  }

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "8px 24px",
          background: "#fff",
          borderBottom: "1px solid #eee",
          fontSize: 14,
        }}
      >
        <span>
          {user?.name} ({user?.role === "admin" ? "管理員" : user?.role === "dept_head" ? "教務主任" : "教師"})
        </span>
        <button
          onClick={logout}
          style={{
            background: "none",
            border: "1px solid #ddd",
            borderRadius: 6,
            padding: "6px 12px",
            cursor: "pointer",
            fontSize: 13,
          }}
        >
          登出
        </button>
      </div>

      {/* Chat */}
      <ChatWindow
        messages={messages}
        loading={loading}
        activeDataCard={activeDataCard}
        onSend={sendMessage}
        onClearDataCard={() => setActiveDataCard(null)}
      />
    </div>
  );
}

export default App;