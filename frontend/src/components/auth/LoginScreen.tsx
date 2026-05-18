import { useState } from "react";
import type { FormEvent } from "react";

interface LoginScreenProps {
  onLogin: (username: string, password: string) => Promise<void>;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onLogin(username, password);
    } catch {
      setError("帳號或密碼錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>成績管理系統</h1>
        <p style={styles.subtitle}>AI 智慧助手</p>
        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            type="text"
            placeholder="帳號"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={styles.input}
            required
          />
          <input
            type="password"
            placeholder="密碼"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            required
          />
          {error && <p style={styles.error}>{error}</p>}
          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "登入中..." : "登入"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  },
  card: {
    background: "#fff",
    borderRadius: 16,
    padding: "48px 40px",
    width: 400,
    boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    textAlign: "center" as const,
    margin: 0,
    color: "#1a1a2e",
  },
  subtitle: {
    textAlign: "center" as const,
    color: "#888",
    marginBottom: 32,
    fontSize: 14,
  },
  form: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 16,
  },
  input: {
    padding: "12px 16px",
    borderRadius: 8,
    border: "1px solid #ddd",
    fontSize: 15,
    outline: "none",
  },
  button: {
    padding: "12px",
    borderRadius: 8,
    border: "none",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "#fff",
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
  },
  error: {
    color: "#e74c3c",
    fontSize: 14,
    textAlign: "center" as const,
    margin: 0,
  },
};