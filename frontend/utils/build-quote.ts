import { compute } from "@/utils/compute";
import { Quote } from "@/types/quote";
import { SolarInput } from "@/features/SolarEstimator";

export function buildQuote(input: SolarInput): Quote {
  const result = compute({
    areaMSq: input.area,
    usable: input.usable / 100,
    efficiency: input.efficiency / 100,
    regionKey: input.regionKey,
    currencyKey: input.currencyKey,
  });

  return {
    input,
    result,
    createdAt: new Date().toISOString(),
  };
}