import { useState, useMemo } from "react";
import type { DataCard } from "../../types";

interface ResultCardProps {
  card: DataCard;
  onClose: () => void;
}

type SortDir = "asc" | "desc" | null;

export function ResultCard({ card, onClose }: ResultCardProps) {
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 20;

  const handleSort = (colIndex: number) => {
    if (sortCol === colIndex) {
      setSortDir(sortDir === "asc" ? "desc" : sortDir === "desc" ? null : "asc");
      if (sortDir === "desc") setSortCol(null);
    } else {
      setSortCol(colIndex);
      setSortDir("asc");
    }
    setPage(0);
  };

  const sortedRows = useMemo(() => {
    if (!card.payload?.rows || sortCol === null || sortDir === null) return card.payload?.rows || [];
    const rows = [...card.payload.rows];
    rows.sort((a: any[], b: any[]) => {
      const va = a[sortCol];
      const vb = b[sortCol];
      if (typeof va === "number" && typeof vb === "number") {
        return sortDir === "asc" ? va - vb : vb - va;
      }
      const sa = String(va);
      const sb = String(vb);
      return sortDir === "asc" ? sa.localeCompare(sb) : sb.localeCompare(sa);
    });
    return rows;
  }, [card.payload?.rows, sortCol, sortDir]);

  const totalPages = Math.ceil(sortedRows.length / PAGE_SIZE);
  const pagedRows = sortedRows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  if (card.type === "table") {
    return (
      <div style={styles.card}>
        <div style={styles.header}>
          <h3 style={styles.title}>{card.title}</h3>
          <span style={styles.count}>{sortedRows.length} 筆</span>
          <button onClick={onClose} style={styles.closeBtn}>✕</button>
        </div>
        <div style={styles.tableWrap}>
          <table style={styles.table}>
            <thead>
              <tr>
                {card.payload.columns?.map((col: string, i: number) => (
                  <th
                    key={col}
                    style={{ ...styles.th, cursor: "pointer" }}
                    onClick={() => handleSort(i)}
                  >
                    {col}
                    {sortCol === i && sortDir === "asc" && " ↑"}
                    {sortCol === i && sortDir === "desc" && " ↓"}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pagedRows.map((row: any[], i: number) => (
                <tr key={i}>
                  {row.map((cell: any, j: number) => (
                    <td key={j} style={styles.td}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div style={styles.pagination}>
            <button
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
              style={{ ...styles.pageBtn, opacity: page === 0 ? 0.4 : 1 }}
            >
              上一頁
            </button>
            <span style={styles.pageInfo}>
              {page + 1} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage(page + 1)}
              style={{ ...styles.pageBtn, opacity: page >= totalPages - 1 ? 0.4 : 1 }}
            >
              下一頁
            </button>
          </div>
        )}
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
  count: { fontSize: 13, color: "#888", marginRight: 8 },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: 18,
    cursor: "pointer",
    color: "#888",
  },
  tableWrap: {
    maxHeight: 400,
    overflowY: "auto" as const,
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
    position: "sticky" as const,
    top: 0,
    zIndex: 1,
    userSelect: "none" as const,
  },
  td: {
    padding: "8px 12px",
    fontSize: 14,
    borderBottom: "1px solid #eee",
  },
  pagination: {
    display: "flex",
    justifyContent: "center" as const,
    alignItems: "center" as const,
    gap: 12,
    padding: "8px 16px",
    borderTop: "1px solid #eee",
  },
  pageBtn: {
    padding: "6px 12px",
    border: "1px solid #ddd",
    borderRadius: 4,
    background: "#fff",
    cursor: "pointer",
    fontSize: 13,
  },
  pageInfo: {
    fontSize: 13,
    color: "#666",
  },
  pre: {
    padding: 16,
    fontSize: 13,
    background: "#f5f6fa",
    overflow: "auto" as const,
  },
};