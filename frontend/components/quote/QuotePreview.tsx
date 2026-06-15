import { Quote } from "@/types/quote";
import { fmt } from "@/utils/format";
import MetricCard from "@/components/display/MetricCard";
import BreakdownRow from "@/components/display/BreakDownRow";
import { useRef } from "react";
import { exportQuotePdf } from "@/utils/export-quote-pdf";

type Props = {
  quote: Quote;
};


export default function QuotePreview({ quote }: Props) {
  const quoteRef = useRef<HTMLDivElement>(null);

  const r = quote.result;


  return (
    <div className="space-y-6">
      {/* PDF BUTTON */}
      <div className="flex justify-end">
        <button
          onClick={() => {
            if (!quoteRef.current) return;
            exportQuotePdf(quoteRef.current, `solar-quote.pdf`);
          }}
          className="bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition"
        >
          Download PDF
        </button>
      </div>

      {/* QUOTE CONTENT */}
      <div ref={quoteRef} className="bg-white p-6 border rounded-xl">
        <h1 className="text-2xl font-semibold mb-6">Solar Quote</h1>

        {/* Customer */}
        <div className="mb-6">
          <div className="font-medium">{quote.input.customerName}</div>
          <div className="text-sm text-gray-500">{quote.input.email}</div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <MetricCard
            label="System size"
            value={`${r.systemKw.toFixed(1)} kW`}
          />
          <MetricCard label="Panels" value={`${r.numPanels}`} />
          <MetricCard label="Total cost" value={fmt(r.sym, r.totalCost)} />
          <MetricCard
            label="Annual savings"
            value={fmt(r.sym, r.annualSaving)}
          />
        </div>

        {/* Breakdown */}
        <div className="border rounded-xl p-4 space-y-2">
          <div className="text-sm font-medium text-gray-500 mb-2">
            Cost breakdown
          </div>

          <BreakdownRow
            label="Panels & hardware"
            value={fmt(r.sym, r.hardware)}
          />
          <BreakdownRow label="Inverter" value={fmt(r.sym, r.inverter)} />
          <BreakdownRow label="Labour" value={fmt(r.sym, r.labour)} />
          <BreakdownRow label="Misc" value={fmt(r.sym, r.misc)} />
          <BreakdownRow
            label="Total"
            value={fmt(r.sym, r.totalCost)}
            bold
          />
        </div>
      </div>
    </div>
  );
}