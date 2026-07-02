"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import QuotePreview from "@/components/quote/QuotePreview";
import { getQuote } from "@/utils/quote-store";
import { Quote } from "@/types/quote";
import { decodeQuote } from "@/utils/quote-url";

function QuoteContent() {
  const params = useSearchParams();
  const data = params.get("data");

  if (!data) {
    return <div className="p-6">No quote found</div>;
  }

  let quote;

  try {
    quote = decodeQuote(data);
  } catch {
    return <div className="p-6">Invalid or corrupted quote</div>;
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <QuotePreview quote={quote} />
    </div>
  );
}

export default function QuotePage() {
  return (
    <Suspense fallback={<div className="p-6">Loading...</div>}>
      <QuoteContent />
    </Suspense>
  );
}