type CustomerData = {
  customerName: string;
  email: string;
  phoneNumber: string;
  projectDescription: string;
  installationAddress: string;
  notes: string;
};

type Props = {
  data: CustomerData;
  onChange: (data: CustomerData) => void;
};

export default function CustomerForm({ data, onChange }: Props) {
  function update<K extends keyof CustomerData>(
    key: K,
    value: CustomerData[K]
  ) {
    onChange({
      ...data,
      [key]: value,
    });
  }

  return (
    <section style={styles.section}>
      <h3 style={styles.sectionTitle}>Customer Details</h3>

      <div style={styles.row}>
        <Input
          label="Customer Name"
          value={data.customerName}
          onChange={(v) => update("customerName", v)}
        />
        <Input
          label="Email"
          value={data.email}
          onChange={(v) => update("email", v)}
        />
        <Input
          label="Phone Number"
          value={data.phoneNumber}
          onChange={(v) => update("phoneNumber", v)}
        />
      </div>

      <div style={styles.row}>
        
        <Textarea
          label="Project Description"
          value={data.projectDescription}
          onChange={(v) => update("projectDescription", v)}
        />
      </div>

      <div style={styles.row}>
        <Textarea
          label="Installation Address (Optional)"
          value={data.installationAddress}
          onChange={(v) => update("installationAddress", v)}
        />
        <Textarea
          label="Notes / Special Requirements"
          value={data.notes}
          onChange={(v) => update("notes", v)}
        />
      </div>
    </section>
  );
}

type InputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

function Input({ label, value, onChange }: InputProps) {
  return (
    <div style={styles.field}>
      <label style={styles.label}>{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={styles.input}
      />
    </div>
  );
}

type TextareaProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

function Textarea({ label, value, onChange }: TextareaProps) {
  return (
    <div style={styles.field}>
      <label style={styles.label}>{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ ...styles.input, height: 80 }}
      />
    </div>
  );
}

const styles = {
  section: { padding: "1.25rem 1.5rem" },
  sectionTitle: {
    margin: "0 0 1rem",
    fontSize: 14,
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: "#9ca3af",
  },
  row: {
    display: "flex",
    gap: 12,
    marginBottom: 12,
    flexWrap: "wrap" as const,
  },
  field: { flex: "1 1 180px" },
  label: {
    fontSize: 12,
    color: "#6b7280",
    marginBottom: 5,
    display: "block",
  },
  input: {
    width: "100%",
    padding: "8px 10px",
    border: "1px solid #d1d5db",
    borderRadius: 8,
    fontSize: 14,
  },
};

