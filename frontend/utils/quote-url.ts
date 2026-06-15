import LZString from "lz-string";
import { Quote } from "@/types/quote";

export function encodeQuote(q: Quote): string {
  const json = JSON.stringify(q);
  return LZString.compressToEncodedURIComponent(json);
}

export function decodeQuote(data: string): Quote {
  const json = LZString.decompressFromEncodedURIComponent(data);

  if (!json) {
    throw new Error("Invalid or corrupted quote data");
  }

  return JSON.parse(json);
}