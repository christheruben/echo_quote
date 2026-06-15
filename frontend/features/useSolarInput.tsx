"use client";

import { useState } from "react";
import { SolarInput } from "@/features/SolarEstimator";

export function useSolarInput(initial: SolarInput) {
  const [input, setInput] = useState<SolarInput>(initial);

  const update = <K extends keyof SolarInput>(
    key: K,
    value: SolarInput[K]
  ) => {
    setInput((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const reset = () => setInput(initial);

  return {
    input,
    setInput,
    update,
    reset,
  };
}