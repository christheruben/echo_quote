"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

// constants
import { REGIONS } from "@/constants";
import { Quote } from "@/types/quote";

// components
import MetricCard from "../components/display/MetricCard";
import BreakdownRow from "../components/display/BreakDownRow";

// features
import SolarEstimator, { SolarInput } from "@/features/SolarEstimator";
import { useSolarInput } from "@/features/useSolarInput";
// utils
import { compute } from "@/utils/compute";
import { fmt } from "@/utils/format";
import { encodeQuote } from "@/utils/quote-url";
import { buildQuote } from "@/utils/build-quote";



const initialState: SolarInput = {
  area: 100,
  unit: "m²",
  regionKey: "za",
  currencyKey: "USD",
  efficiency: 20,
  usable: 80,

  customerName: "",
  email: "",
  phoneNumber: "",
  companyName: "",
  projectDescription: "",
  installationAddress: "",
  notes: "",
};

export default function Estimator() {
  const router = useRouter();

  const { input, setInput } = useSolarInput(initialState);
  const [quote, setQuote] = useState<Quote | null>(null);

  // Recompute results whenever input changes
  useEffect(() => {
  const result = compute({
    areaMSq: input.area,
    usable: input.usable / 100,
    efficiency: input.efficiency / 100,
    regionKey: input.regionKey,
    currencyKey: input.currencyKey,
  });

  setQuote(buildQuote(input));
  }, [input]);

  if (!quote) return null;

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 text-gray-900">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className="text-3xl">☀</div>
        <div>
          <h2 className="text-xl font-semibold">Solar Cost Estimator</h2>
          <p className="text-sm text-gray-500">
            Estimate installation cost from your roof area
          </p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
        {/* Input */}
        <div className="p-6 border-b border-gray-100">
          <SolarEstimator value={input} onChange={setInput} />
        </div>

        {/* Results */}
        <div className="p-6 space-y-6">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Estimate
          </h3>

          {/* Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard
              label="System size"
              value={`${quote.result.systemKw.toFixed(1)} kW`}
              sub={`~${quote.result.numPanels} panels`}
            />
            <MetricCard
              label="Total cost"
              value={fmt(quote.result.sym, quote.result.totalCost)}
            />
            <MetricCard
              label="Annual output"
              value={`${Math.round(quote.result.annualKwh).toLocaleString()} kWh`}
              sub={`${REGIONS[input.regionKey].peakSun}h sun/day`}
            />
            <MetricCard
              label="Annual savings"
              value={fmt(quote.result.sym, quote.result.annualSaving)}
              sub={`at ${quote.result.sym}${quote.result.elecRate}/kWh`}
            />
          </div>
        
          {/* Breakdown
          <div className="border border-gray-100 rounded-xl p-4 space-y-2">
            <div className="text-sm font-medium text-gray-500 mb-2">
              Cost breakdown
            </div>
          
            <BreakdownRow
              label="Panels & hardware (50%)"
              value={fmt(quote.result.sym, quote.result.hardware)}
            />
            <BreakdownRow
              label="Inverter (15%)"
              value={fmt(quote.result.sym, quote.result.inverter)}
            />
            <BreakdownRow
              label="Installation labour (25%)"
              value={fmt(quote.result.sym, quote.result.labour)}
            />
            <BreakdownRow
              label="Wiring, permits (10%)"
              value={fmt(quote.result.sym, quote.result.misc)}
            />
            <BreakdownRow
              label="Total"
              value={fmt(quote.result.sym, quote.result.totalCost)}
              bold
            />
          </div>  */}


          {/* Payback */}
          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-gray-500">
                Payback period
              </span>

              <span
                className={`text-xs px-2 py-1 rounded-full font-medium ${
                  quote.result.payback <= 8
                    ? "bg-green-100 text-green-700"
                    : "bg-yellow-100 text-yellow-700"
                }`}
              >
                {quote.result.payback <= 8 ? "Strong ROI" : "Moderate ROI"}
              </span>
            </div>

            <div className="text-2xl font-semibold">
              {isFinite(quote.result.payback)
                ? `${quote.result.payback.toFixed(1)} years`
                : "—"}
            </div>

            <div className="text-sm text-gray-500 mt-1">
              25-year net gain:{" "}
              <span className="font-semibold">
                {fmt(quote.result.sym, quote.result.net25)}
              </span>
            </div>
          </div>
          {/* Generate Quote Button */}
          <div>
            <button
              onClick={() => {
                const quote = buildQuote(input);

                const encoded = encodeQuote(quote);

                router.push(`/quote?data=${encoded}`);
              }}
              className="
                w-full
                bg-black
                hover:bg-green-600
                text-white
                font-medium
                py-3
                px-4
                rounded-lg
                transition-colors
              "
            >
              Generate Quote
            </button>
          </div>
        </div>
      </div>

      <p className="text-xs text-gray-500 text-center mt-6 leading-relaxed">
        Estimates only. Actual costs vary by installer, panel brand, roof type,
        and local tariffs. Always get a professional quote.
      </p>
    </div>
  );
}