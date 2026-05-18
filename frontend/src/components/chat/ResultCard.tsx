import type { DataCard } from "../../types";

interface ResultCardProps {
  card: DataCard;
  onClose: () => void;
}

export function ResultCard({ card, onClose }: ResultCardProps) {
  if (card.type === "table") {
    return (
      <div style={styles.card}>
        <div style={styles.header}>
          <h3 style={styles.title}>{card.title}</h3>
          <button onClick={onClose} style={styles.closeBtn}>✕</button>
        </div>
        <table style={styles.table}>
          <thead>
            <tr>
              {card.payload.columns?.map((col: string) => (
                <th key={col} style={styles.th}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {card.payload.rows?.map((row: any[], i: number) => (
              <tr key={i}>
                {row.map((cell: any, j: number) => (
                  <td key={j} style={styles.td}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Default: show raw data
  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <h3 style={styles.title}>{card.title}</h3>
        <button onClick={onClose} style={styles.closeBtn}>✕</button>
      </div>
      <pre style={styles.pre}>{JSON.stringify(card.payload, null, 2)}</pre>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: "#fff",
    borderRadius: 8,
    border: "1px solid #eee",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    justifyContent: "space-between" as const,
    alignItems: "center" as const,
    padding: "12px 16px",
    borderBottom: "1px solid #eee",
  },
  title: { fontSize: 16, fontWeight: 600, margin: 0 },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: 18,
    cursor: "pointer",
    color: "#888",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse" as const,
  },
  th: {
    padding: "8px 12px",
    background: "#f5f6fa",
    fontSize: 13,
    fontWeight: 600,
    textAlign: "left" as const,
  },
  td: {
    padding: "8px 12px",
    fontSize: 14,
    borderBottom: "1px solid #eee",
  },
  pre: {
    padding: 16,
    fontSize: 13,
    background: "#f5f6fa",
    overflow: "auto" as const,
  },
};