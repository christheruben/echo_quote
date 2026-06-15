"use client";

import NumberInput from "@/components/inputs/NumberInput";
import Select from "@/components/inputs/Select";

import {
  REGIONS,
  CURRENCIES,
  EFFICIENCY_OPTIONS,
  USABLE_OPTIONS,
  RegionKey,
  CurrencyKey,
} from "@/constants";

export type SolarInput = {
  area: number;
  unit: "m²" | "ft²";
  regionKey: RegionKey;
  currencyKey: CurrencyKey;
  efficiency: number;
  usable: number;

  customerName: string;
  email: string;
  phoneNumber: string;
  companyName: string;
  projectDescription: string;
  installationAddress: string;
  notes: string;
};

type Props = {
  value: SolarInput;
  onChange: (next: SolarInput) => void;
};

export default function SolarEstimator({ value, onChange }: Props) {
  function update<K extends keyof SolarInput>(key: K, val: SolarInput[K]) {
    onChange({ ...value, [key]: val });
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
        Input details
      </h2>

      {/* Roof */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <NumberInput
          label="Roof area"
          value={value.area}
          unit={value.unit}
          unitOptions={["m²", "ft²"]}
          onChange={(v) => update("area", v)}
          onUnitChange={(u) => update("unit", u as "m²" | "ft²")}
        />

        <Select
          label="Usable area"
          value={value.usable}
          onChange={(v) => update("usable", Number(v))}
          options={USABLE_OPTIONS}
        />
      </div>

      {/* System */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Select
          label="Region"
          value={value.regionKey}
          onChange={(v) => update("regionKey", v as RegionKey)}
          options={Object.entries(REGIONS).map(([k, r]) => ({
            value: k,
            label: r.label,
          }))}
        />

        <Select
          label="Currency"
          value={value.currencyKey}
          onChange={(v) => update("currencyKey", v as CurrencyKey)}
          options={Object.keys(CURRENCIES).map((k) => ({
            value: k,
            label: k,
          }))}
        />

        <Select
          label="Panel efficiency"
          value={value.efficiency}
          onChange={(v) => update("efficiency", Number(v))}
          options={EFFICIENCY_OPTIONS}
        />
      </div>

      {/* Customer */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <input
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Customer name"
          value={value.customerName}
          onChange={(e) => update("customerName", e.target.value)}
        />

        <input
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Email"
          value={value.email}
          onChange={(e) => update("email", e.target.value)}
        />

        <input
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Phone"
          value={value.phoneNumber}
          onChange={(e) => update("phoneNumber", e.target.value)}
        />
      </div>
    </div>
  );
}