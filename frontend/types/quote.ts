import { SolarInput } from "@/features/SolarEstimator";

export type Quote = {
  input: SolarInput;
  result: {
    systemKw: number;
    numPanels: number;
    annualKwh: number;
    annualSaving: number;
    totalCost: number;

    hardware: number;
    inverter: number;
    labour: number;
    misc: number;

    payback: number;
    net25: number;
    sym: string;
    elecRate: number;
  };

  createdAt: string;
};