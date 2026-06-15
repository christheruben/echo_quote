// NOT USED ANYMORE, but keeping it for now in case we want to support quote storage in the future

import { Quote } from "@/types/quote";

const KEY = "quotes";

function isBrowser() {
  return typeof window !== "undefined";
}

function generateId() {
  return crypto.randomUUID();
}

export function saveQuote(quote: Quote): string {
  if (!isBrowser()) return "";

  const id = generateId();

  const existing = JSON.parse(localStorage.getItem(KEY) || "{}");

  existing[id] = quote;

  localStorage.setItem(KEY, JSON.stringify(existing));

  return id;
}

export function getQuote(id: string): Quote | null {
  if (!isBrowser()) return null;

  const existing = JSON.parse(localStorage.getItem(KEY) || "{}");
  return existing[id] || null;
}