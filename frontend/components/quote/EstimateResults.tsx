import MetricCard from "@/components/display/MetricCard";
import BreakdownRow from "@/components/display/BreakDownRow";
import { REGIONS, RegionKey } from "@/constants/regions";
import { fmt } from "@/utils/format";

type Props = {
  result: any;
  regionKey: RegionKey;
};

export default function EstimateResults({ result, regionKey }: Props) {
  if (!result) return null;

  const r = result;

  return (
    <section style={styles.section}>
      <h3 style={styles.sectionTitle}>Estimate</h3>

      {/* Metrics */}
      <div style={styles.metricGrid}>
        <MetricCard
          label="System size"
          value={`${r.systemKw.toFixed(1)} kW`}
          sub={`~${r.numPanels} panels`}
        />
        <MetricCard
          label="Total installed cost"
          value={fmt(r.sym, r.totalCost)}
        />
        <MetricCard
          label="Annual output"
          value={`${Math.round(r.annualKwh).toLocaleString()} kWh`}
          sub={`${REGIONS[regionKey].peakSun}h peak sun/day`}
        />
        <MetricCard
          label="Annual savings"
          value={fmt(r.sym, r.annualSaving)}
          sub={`at ${r.sym}${r.elecRate}/kWh`}
        />
      </div>

      {/* Breakdown */}
      <div style={styles.breakdown}>
        <div style={styles.label}>Cost breakdown</div>
        <BreakdownRow label="Panels & hardware (50%)" value={fmt(r.sym, r.hardware)} />
        <BreakdownRow label="Inverter (15%)" value={fmt(r.sym, r.inverter)} />
        <BreakdownRow label="Installation labour (25%)" value={fmt(r.sym, r.labour)} />
        <BreakdownRow label="Wiring, permits, misc (10%)" value={fmt(r.sym, r.misc)} />
        <BreakdownRow label="Total" value={fmt(r.sym, r.totalCost)} bold />
      </div>

      {/* Payback */}
      <div style={styles.payback}>
        <div style={{ display: "flex", gap: 10 }}>
          <span style={styles.label}>Payback period</span>
          <span style={r.payback <= 8 ? styles.green : styles.amber}>
            {r.payback <= 8 ? "Strong ROI" : "Moderate ROI"}
          </span>
        </div>

        <div style={styles.paybackYears}>
          {isFinite(r.payback) ? `${r.payback.toFixed(1)} years` : "—"}
        </div>

        <div style={styles.sub}>
          25-year net gain: <strong>{fmt(r.sym, r.net25)}</strong>
        </div>
      </div>
    </section>
  );
}

// ─── Styles ───

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
  metricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
    gap: 10,
    marginBottom: "1.25rem",
  },
  breakdown: {
    border: "1px solid #f3f4f6",
    borderRadius: 10,
    padding: "0.75rem 1rem",
    marginBottom: "1rem",
  },
  label: {
    fontSize: 12,
    color: "#6b7280",
    marginBottom: 6,
  },
  payback: {
    background: "#f9fafb",
    border: "1px solid #f3f4f6",
    borderRadius: 10,
    padding: "0.875rem 1rem",
  },
  paybackYears: {
    fontSize: 26,
    fontWeight: 600,
    margin: "6px 0",
  },
  sub: {
    fontSize: 13,
    color: "#6b7280",
  },
  green: {
    background: "#dcfce7",
    color: "#15803d",
    padding: "3px 9px",
    borderRadius: 99,
    fontSize: 11,
  },
  amber: {
    background: "#fef9c3",
    color: "#92400e",
    padding: "3px 9px",
    borderRadius: 99,
    fontSize: 11,
  },
};