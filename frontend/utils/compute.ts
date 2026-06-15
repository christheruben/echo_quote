// This file contains the core logic for computing the solar panel quote based on user input and region/currency data.

import { REGIONS } from "@/constants/regions";
import { CURRENCIES } from "@/constants/currencies";

type ComputeInput = {
  areaMSq: number;
  usable: number;
  efficiency: number;
  regionKey: keyof typeof REGIONS;
  currencyKey: keyof typeof CURRENCIES;
};

export function compute({
  areaMSq,
  usable,
  efficiency,
  regionKey,
  currencyKey,
}: ComputeInput) {
  const region = REGIONS[regionKey];
  const cur = CURRENCIES[currencyKey];

  const usableArea = areaMSq * usable;

  const systemKw = usableArea * efficiency;

  const numPanels = Math.max(0, Math.round(usableArea / 1.8));

  const annualKwh = systemKw * region.peakSun * 365;

  const annualSaving = annualKwh * cur.elecRate;

  const totalCost = systemKw * 1000 * cur.installPerW;

  const hardware = totalCost * 0.5;
  const inverter = totalCost * 0.15;
  const labour = totalCost * 0.25;
  const misc = totalCost * 0.1;

  const payback = annualSaving > 0 ? totalCost / annualSaving : Infinity;

  const net25 = annualSaving * 25 - totalCost;

  return {
    systemKw,
    numPanels,
    annualKwh,
    annualSaving,
    totalCost,
    hardware,
    inverter,
    labour,
    misc,
    payback,
    net25,
    sym: cur.sym,
    elecRate: cur.elecRate,
  };
}