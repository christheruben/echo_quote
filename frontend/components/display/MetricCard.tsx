type MetricCardProps = {
  label: string;
  value: string;
  sub?: string;
};

export default function MetricCard({ label, value, sub }: MetricCardProps) {
  return (
    <div style={styles.metricCard}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
      {sub && <div style={styles.metricSub}>{sub}</div>}
    </div>
  );
}

const styles = {
  metricCard: {
    background: "#f9fafb",
    border: "1px solid #f3f4f6",
    borderRadius: 10,
    padding: "0.75rem 1rem",
  },
  metricLabel: {
    fontSize: 11,
    color: "#9ca3af",
    marginBottom: 4,
    fontWeight: 500,
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 600,
    color: "#111827",
  },
  metricSub: {
    fontSize: 11,
    color: "#9ca3af",
    marginTop: 2,
  },
};