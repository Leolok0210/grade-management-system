import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";

interface ChartPayload {
  chart_type: "bar" | "scatter" | "pie";
  x_key: string;
  y_key: string;
  data: Record<string, any>[];
  x_label?: string;
  y_label?: string;
  colors?: string[];
}

interface ChartCardProps {
  title: string;
  payload: ChartPayload;
}

const DEFAULT_COLORS = [
  "#4f46e5",
  "#06b6d4",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
];

function ChartContent({ payload, colors }: { payload: ChartPayload; colors: string[] }) {
  if (payload.chart_type === "pie") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={payload.data}
            dataKey={payload.y_key}
            nameKey={payload.x_key}
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ name, value }) => `${name}: ${value}`}
          >
            {payload.data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (payload.chart_type === "scatter") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey={payload.x_key}
            name={payload.x_label || payload.x_key}
            type="number"
          />
          <YAxis
            dataKey={payload.y_key}
            name={payload.y_label || payload.y_key}
            type="number"
          />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={payload.data} fill={colors[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  // bar chart
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={payload.data} margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey={payload.x_key}
          angle={-45}
          textAnchor="end"
          interval={0}
          height={80}
          tick={{ fontSize: 12 }}
        />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey={payload.y_key} fill={colors[0]}>
          {payload.data.map((_, i) => (
            <Cell key={i} fill={colors[i % colors.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ChartCard({ title, payload }: ChartCardProps) {
  const [expanded, setExpanded] = useState(false);
  const colors = payload.colors || DEFAULT_COLORS;

  const chartTypeLabel: Record<string, string> = {
    bar: "長條圖",
    scatter: "散點圖",
    pie: "圓餅圖",
  };

  return (
    <div style={styles.container}>
      <button onClick={() => setExpanded(!expanded)} style={styles.toggleBtn}>
        <span style={styles.arrow}>{expanded ? "▼" : "▶"}</span>
        <span style={styles.toggleTitle}>
          {title || chartTypeLabel[payload.chart_type] || "圖表"}
        </span>
      </button>
      {expanded && (
        <div style={styles.chartArea}>
          <ChartContent payload={payload} colors={colors} />
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "8px 0",
  },
  toggleBtn: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "6px 12px",
    borderRadius: 6,
    width: "100%",
    textAlign: "left",
    fontSize: 14,
    color: "#4f46e5",
    fontWeight: 500,
  },
  arrow: {
    fontSize: 12,
    transition: "transform 0.2s",
  },
  toggleTitle: {
    flex: 1,
  },
  chartArea: {
    marginTop: 8,
    paddingLeft: 12,
  },
};
