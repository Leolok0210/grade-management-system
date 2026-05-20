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

export function ChartCard({ title, payload }: ChartCardProps) {
  const colors = payload.colors || DEFAULT_COLORS;

  if (payload.chart_type === "pie") {
    return (
      <div style={styles.container}>
        <h4 style={styles.title}>{title}</h4>
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
      </div>
    );
  }

  if (payload.chart_type === "scatter") {
    return (
      <div style={styles.container}>
        <h4 style={styles.title}>{title}</h4>
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
      </div>
    );
  }

  // Default: bar chart
  return (
    <div style={{ ...styles.container, minWidth: 0 }}>
      <h4 style={styles.title}>{title}</h4>
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
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "12px 16px",
  },
  title: {
    fontSize: 14,
    fontWeight: 600,
    margin: "0 0 8px 0",
    color: "#333",
  },
};
