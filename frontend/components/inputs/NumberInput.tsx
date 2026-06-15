type UnitOption = string;

type NumberInputProps = {
  label: string;
  value: number | string;
  onChange: (value: number) => void;
  unit?: string;
  onUnitChange?: (unit: string) => void;
  unitOptions?: UnitOption[];
};

export default function NumberInput({
  label,
  value,
  onChange,
  unit,
  onUnitChange,
  unitOptions,
}: NumberInputProps) {
  return (
    <div style={styles.field}>
      <label style={styles.label}>{label}</label>

      <div style={styles.row}>
        <input
          type="number"
          min={0}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          style={styles.input}
        />

        {unitOptions && unit && onUnitChange && (
          <select
            value={unit}
            onChange={(e) => onUnitChange(e.target.value)}
            style={styles.select}
          >
            {unitOptions.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}

const styles = {
  field: {
    flex: "1 1 180px",
    minWidth: 0,
  },
  label: {
    display: "block",
    fontSize: 12,
    color: "#6b7280",
    marginBottom: 5,
  },
  row: {
    display: "flex",
    gap: 8,
  },
  input: {
    width: "100%",
    padding: "8px 10px",
    border: "1px solid #d1d5db",
    borderRadius: 8,
    fontSize: 14,
    outline: "none",
  },
  select: {
    width: 72,
    padding: "8px 10px",
    border: "1px solid #d1d5db",
    borderRadius: 8,
    fontSize: 14,
    background: "#fff",
    cursor: "pointer",
  },
};