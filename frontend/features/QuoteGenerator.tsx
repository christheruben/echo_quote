"use client";

import { useState } from "react";
import { buildQuote } from "@/utils/build-quote";
import QuotePreview from "@/components/quote/QuotePreview";
import { Quote } from "@/types/quote";
import { SolarInput } from "./SolarEstimator";

type Props = {
  input: SolarInput;
};

export default function QuoteGenerator({ input }: Props) {
  const [quote, setQuote] = useState<Quote | null>(null);

  const handleGenerateQuote = () => {
    const generatedQuote = buildQuote(input);
    setQuote(generatedQuote);
  };

  return (
    <div>
      <button onClick={handleGenerateQuote} style={styles.button}>
        Generate Quote
      </button>

      {quote && <QuotePreview quote={quote} />}
    </div>
  );
}

const styles = {
  button: {
    marginTop: 20,
    padding: "10px 14px",
    borderRadius: 8,
    background: "#4caf50",
    color: "#fff",
    border: "none",
    cursor: "pointer",
  },
};