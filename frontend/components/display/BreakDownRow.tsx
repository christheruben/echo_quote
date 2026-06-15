type BreakdownRowProps = {
  label: string;
  value: string;
  bold?: boolean;
};

export default function BreakdownRow({ label, value, bold }: BreakdownRowProps) {
  return (
    <div
      style={{
        ...styles.row,
        fontWeight: bold ? 600 : 400,
      }}
    >
      <span style={{ color: bold ? "inherit" : "#6b7280" }}>
        {label}
      </span>
      <span>{value}</span>
    </div>
  );
}

const styles = {
  row: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: 13,
    padding: "5px 0",
    borderBottom: "1px solid #f9fafb",
    color: "#111827",
  },
};